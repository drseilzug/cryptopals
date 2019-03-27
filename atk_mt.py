from mersenne import Mersenne


class MT32Dbl(Mersenne):
    def __init__(self, seed=5489):
        super().__init__(seed, 32)
        self.state_cands_t = [[]]*self.n*2  # tempered candidates
        self.state_cands_u = [[]]*self.n*2  # untempered candidates
        self.target_values = []*self.n
        self.base_values = []*self.n
        self.valid_states = 0
        self.valid_start_index = None

    def split_ab(self, dbl):
        mask_a = ((1 << 27) - 1) << 26
        mask_b = (1 << 26) - 1
        dbl *= 9007199254740992
        dbl = int(dbl)
        a = dbl & mask_a
        a >>= 26
        b = dbl & mask_b
        a <<= 5
        b <<= 6
        return a, b

    def get_double_ab(self, a, b):
        """ Uses up 2 output to get a double value mimicking what pythons
        Random module does"""
        a >>= 5
        b >>= 6
        return (a*67108864.0+b) * (1.0/9007199254740992.0)

    def gen_candidates(self, index, value, var_bits):
        """generates a list of all possible statevalues for given index
        that match value on all non var_bits (var_bits counted from right i.e. least significant bits)
        and if available the list of possible
        state values already present in self.state_candidates.
        Possible candidates are returned as a list.

        the variable bit positions of value are expected to be 0
        """
        mask_fix = ((1 << self.word) - 1) << var_bits
        mask_var = (1 << var_bits) - 1
        if value & mask_var != 0:  # error indicates undesirable input states
            raise ValueError("Var Bits set in value.")
        candidates = []
        # check for already present candidates list
        if len(self.state_cands_t[index]) > 0:
            pre_candidates = self.state_cands_t[index]
            for c in pre_candidates:
                if c & mask_fix == value:
                    candidates.append(c)
        else:
            for fill_bits in range(0, 1 << var_bits):
                candidates.append(value + fill_bits)
        if len(candidates) == 0:
            raise ValueError("Failed to find candidate for index {}. Assume Bad Data.".format(index))
        return candidates

    def check_set_abx(self, a_flag, b, x, target):
        """generates 3 state values from candidates,
        twists to get new state value and checks if they correspond
        to target double (upper bits)
        """
        if a_flag:
            state_a = self.upper_mask
        else:
            state_a = 0
        state_b = self.untemper(b)
        state_x = self.untemper(x)
        candidate_state = self.single_twist(state_a, state_b, state_x)
        candidate_state_t = self.temper(candidate_state)
        target_state_t, _ = self.split_ab(target)
        return target_state_t >> 5 == candidate_state_t >> 5

    def check_set_bcy(self, b_flag, c, y, target):
        """generates 3 state values from candidates,
        twists to get new state value and checks if they correspond
        to target double (lower bits)
        """
        if b_flag:
            state_b = self.upper_mask
        else:
            state_b = 0
        state_c = self.untemper(c)
        state_y = self.untemper(y)
        candidate_state = self.single_twist(state_b, state_c, state_y)
        candidate_state_t = self.temper(candidate_state)
        _, target_state_t = self.split_ab(target)
        return target_state_t >> 6 == candidate_state_t >> 6

    def update_candidates(self, index, candidates):
        """Writes tempered candidates"""
        if len(candidates) == 0:
            raise ValueError("No valid Candidate for index {}. Presumably Bad Data".format(index))
        c_set = set(candidates)
        candidates = list(c_set)
        self.state_cands_t[index] = candidates

    def untemper_candidates(self):
        for index, candidates in enumerate(self.state_cands_t):
            self.state_cands_u[index] = []
            for candidate in candidates:
                # may need a try block to skip invalid candidates if untemper can detect
                self.state_cands_u[index].append(self.untemper(candidate))

    def update_valid_states(self):  # not working conceptually
        count = 1
        index = 0
        while True:
            try:
                if len(self.state_cands_u[index]) != 1:
                    index += 1
                else:
                    break
            except IndexError:
                self.valid_states = 0
                return None
        for n in range(624):
            count *= len(self.state_cands_u[index + n])
        self.valid_states = count
        self.valid_start_index = index

    def build_state(self, rep_advance=0):
        """builds generator state from the candidates revocered by
        self.build_cands_dbl if an unambiguous state is found

        generator is initialized at the first unambiguous data index found
        and then advanced by rep_advance steps"""
        if self.valid_states != 1:
            msg = """No unambiguous state found. valid states = {}.
            If valid states are not 0 you can try to manually build the states from
            the data in self.state_cands_u""".format(self.valid_states)
            print(msg)
        for i in range(self.valid_start_index, self.valid_start_index + self.n):
            self.state[i - self.valid_start_index] = self.state_cands_u[i]
        self.index = 0
        for i in range(rep_advance):
            self.get_value()

    def sync_state(self, dbl_list):
        """ TODO """
        raise NotImplementedError()

    def split_high_low(self, candidates):
        """Splits candidates into "high" and "low" candidates
        high :: most significant bit after untemper is 1
        low :: most significant bit after untemper is 0
        """
        high = []
        low = []
        for candidate in candidates:
            if self.untemper(candidate) >> 31 == 1:
                high.append(candidate)
            elif self.untemper(candidate) >> 31 == 0:
                low.append(candidate)
            else:
                raise RuntimeError("this should not happen! DEBUG this!")
        return (high, low)

    def verify_candidates(self, cands_a, cands_b, cands_x, target, bcy):
        high_a, low_a = self.split_high_low(cands_a)
        valid_a_high, valid_a_low = False, False
        valid_bx = []  # list of possible b/x combinations (can we save time by saving this realtion?? TODO)
        if not bcy:
            check_fun = self.check_set_abx
        else:
            check_fun - self.check_set_bcy
        for b in cands_b:
            for x in cands_x:
                if len(high_a) > 0 and self.check_fun(True, b, x, target):
                    valid_bx.append((b, x))
                    valid_a_high = True
                if len(low_a) > 0 and self.check_fun(False, b, x, target):
                    valid_bx.append((b, x))
                    valid_a_low = True
        cands_a = []
        cands_b = []
        cands_x = []
        if valid_a_high:
            cands_a += high_a
        if valid_a_low:
            cands_a += low_a
        for b, x in valid_bx:
            cands_b.append(b)
            cands_x.append(x)
        return (cands_a, cands_b, cands_x)

    def build_cands_dbl(self, list_in):
        if len(list_in) < 624:
            raise ValueError("To few values given. need at least 624 consequtive double outputs from target generator")
        self.base_values = list_in[:]
        self.target_values = list_in[312:624]
        for index, target in enumerate(self.target_values):
            # index of corresposind state values since 1 dbl ~ 2 state values
            index_a = index*2
            index_b = index_a + 1
            index_c = index_a + 2
            index_x = index_a + self.m
            index_y = index_x + 1
            # get corresponding tempered values
            a, b = self.split_ab(self.base_values[index])
            varb_a, varb_b = 5, 6
            c, _ = self.split_ab(self.base_values[index + 1])
            varb_c = 5
            _, x = self.split_ab(self.base_values[index_x//2])  # index_x should always be odd for 32bit version
            varb_x = 6
            y, _ = self.split_ab(self.base_values[index_y//2])
            varb_y = 5

            # get tempered candidate lists
            cands_a = self.gen_candidates(index_a, a, varb_a)
            cands_b = self.gen_candidates(index_b, b, varb_b)
            cands_c = self.gen_candidates(index_c, c, varb_c)
            cands_x = self.gen_candidates(index_x, x, varb_x)
            cands_y = self.gen_candidates(index_y, y, varb_y)

            # Attack 1st state Value (b+x)
            cands_a, cands_b, cands_x = self.verify_candidates(cands_a, cands_a, cands_x, target, False)
            self.update_candidates(index_a, cands_a)
            self.update_candidates(index_b, cands_b)
            self.update_candidates(index_x, cands_x)

            # Attack 2nd state Value (c+y)
            cands_b, cands_c, cands_y = self.verify_candidates(cands_b, cands_c, cands_y, target, True)
            self.update_candidates(index_b, cands_b)
            self.update_candidates(index_c, cands_c)
            self.update_candidates(index_y, cands_y)

            print("Index {} done!".format(index))
        self.untemper_candidates()
        self.update_valid_states()


def main():
    gen = MT32Dbl()
    refgen = MT32Dbl(1)
    doubles = [refgen.get_double() for _ in range(700)]
    gen.build_cands_dbl(doubles)
    print(gen.valid_states)
    return gen, refgen


if __name__ == '__main__':
    gen, refgen = main()
