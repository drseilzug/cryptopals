from mersenne import Mersenne


class MT32Dbl(Mersenne):
    def __init__(self, seed=5489):
        super().__init__(seed, 32)
        self.state_cands_t = [[] for _ in range(self.n*2)]  # tempered candidates
        self.state_cands_u = [[] for _ in range(self.n*2)]  # untempered candidates
        self.target_values = None
        self.base_values = None
        self.valid_states = 0
        self.valid_start_index = None
        self.earliest_state = None

    def split_ab(self, dbl):
        """Returns 2 32bit integers, that would create the input double according to how python generates a double from
        random integers. the last 5 bit of the first output and the last 6 bis fo the secound output are variable and
        get set to 0 bits here.
        NB: algebraically this is a right inverse of get_double_ab wrt. composition but not left inverse
         due to the dropped bits"""
        mask_a = ((1 << 27) - 1) << 26
        mask_b = (1 << 26) - 1
        dbl *= 9007199254740992  # 2^53, the precision of the dbl
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
        """generates a list of all possible tempered statevalues for given index
        that match value on all non var_bits (var_bits counted from right i.e. least significant bits)
        and if available the list of possible tempered
        state values already present in self.state_cands_t.
        Possible candidates are returned as a list.

        the variable bit positions of value are expected to be 0
        """
        mask_var = (1 << var_bits) - 1  # mask matches var bits
        mask_fix = ((1 << self.word) - 1) - mask_var
        if value & mask_var != 0:  # error indicates undesirable input states
            raise ValueError("Var Bits set in value.")
        candidates = []
        # check for already present candidates list otherwise generate all possible values for the varbits
        if len(self.state_cands_t[index]) > 0:
            pre_candidates = self.state_cands_t[index]
            for c in pre_candidates:  # filter candidates for matches with the fixed bits
                if c & mask_fix == value:
                    candidates.append(c)
        else:
            for fill_bits in range(0, 1 << var_bits):
                candidates.append(value + fill_bits)  # this assumes that varbits in value are 0 as checked above
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
        # TODO save the tempered cands states to evaluate whether meaningful reduction to state space
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
        """Writes tempered candidates to self.state_cands_t"""
        if len(candidates) == 0:
            raise ValueError("No valid Candidate for index {}. Presumably Bad Data".format(index))
        candidates[:] = list(set(candidates))  # remove duplicates
        self.state_cands_t[index] = candidates

    def untemper_candidates(self):
        """ Builds self.state_cands_u from self.state_cands_t"""
        for index, candidates in enumerate(self.state_cands_t):
            if len(candidates) == len(self.state_cands_u[index]):
                continue
            self.state_cands_u[index] = []
            for candidate in candidates:
                self.state_cands_u[index].append(self.untemper(candidate))

    def update_valid_states(self):
        best = 0
        best_index = 0
        if len(self.state_cands_u) < self.n:
            self.valid_states = 0
            return None
        for index in range(len(self.state_cands_u) - self.n):
            valid_states = 1
            for i in range(self.n):
                valid_states *= len(self.state_cands_u[index + i])
                if valid_states == 0:
                    break
            if valid_states > 0:
                if best == 0 or valid_states < best:
                    best = valid_states
                    best_index = index
        self.valid_states = best
        self.valid_start_index = best_index

    def build_state(self, rep_advance=0):
        """builds generator state from the candidates recovered by
        self.build_cands_dbl if an unambiguous state is found

        generator is initialized at the first unambiguous data index found
        and then advanced by rep_advance steps"""
        if self.valid_states != 1:
            msg = """No unambiguous state found. valid states = {}.
            If valid states are not 0 you can try to manually build the states from
            the data in self.state_cands_u""".format(self.valid_states)
            print(msg)
        new_state = [cand_list[0] for cand_list in self.state_cands_u[self.valid_start_index:self.valid_start_index+self.n]]
        self.set_state(new_state, 0)
        self.earliest_state = new_state
        # advance the generator by rep_advance steps
        for i in range(rep_advance):
            self.get_value()

    def sync_state(self, dbl_list, max_values=100000):
        """
        This function tries to advance the current state until it matches the end of the double list provided.
        Both possible double alignments will be checked.

        max_values determines how far the generator will try to advance until a partial state match.

        THIS sync assumes that the provided list contains _consecutive_ values by the target generator, that were put out
        after or at worst among the initial values the generator was cloned off.
        sync will fail if list contains values generated from statevalues prior to the cloned generator state.

        if sync fails an ValueError is raised and the generator is reset to the state before calling this
        method"""
        length = len(dbl_list)
        if length == 0:
            raise ValueError('Can not sync to empty list.')
        initial_state = self.get_state()  # save old state
        value_a, value_b = 0, self.get_value()
        values_list = [value_b]
        target = dbl_list[-1]
        for _ in range(max_values+length*2):
            value_a = value_b
            value_b = self.get_value()
            values_list.append(value_b)
            if len(values_list) >= length*2 and self.get_double_ab(value_a, value_b) == target:
                if list(map(self.get_double_ab, values_list[-length*2::2], values_list[-length*2+1::2])) == dbl_list:
                    return None
        # if no match is found in the main loop an error is raised and state reset to what it was before
        self.set_state(*initial_state)
        raise ValueError('could not sync to provided list within {} steps.'.format(max_values))

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
                # if this error occurs it means that somehow a candidate had bits outside the range of a 32bit int set
                raise RuntimeError("this should not happen! DEBUG this!")
        return (high, low)

    def verify_candidates(self, cands_a, cands_b, cands_x, target, bcy):
        """This function filters lists of candidate against a target double value wrt. what combinations
        twist to that double value.
        the Flag bcy determines the orientation of the indices relative to the alignment of double values"""
        high_a, low_a = self.split_high_low(cands_a)  # split according to first bit in A
        valid_a_high, valid_a_low = False, False
        if not bcy:
            check_fun = self.check_set_abx
        else:
            check_fun = self.check_set_bcy

        new_cands_a = []
        new_cands_b = set()
        new_cands_x = set()

        # this could be parallel
        for b in cands_b:
            for x in cands_x:
                if len(high_a) > 0 and check_fun(True, b, x, target):
                    new_cands_b.add(b)
                    new_cands_x.add(x)
                    valid_a_high = True
                if len(low_a) > 0 and check_fun(False, b, x, target):
                    new_cands_b.add(b)
                    new_cands_x.add(x)
                    valid_a_low = True

        # if an a is valid all a with the same first bit are valid since only first bit is relevant in twist
        if valid_a_high:
            new_cands_a += high_a
        if valid_a_low:
            new_cands_a += low_a

        return new_cands_a, list(new_cands_b), list(new_cands_x)

    def build_cands_dbl(self, list_in):
        """This is the core method of this class.
        This method takes a list of 624 _consecutive_ double values that were observed from a python MT generator and
        reverses the generator state of said generator.
        """
        print('[+] Initializing state candidate search.')
        if len(list_in) < 624:
            raise ValueError("To few values given. need at least 624 consecutive double outputs from target generator")
        self.base_values = list_in[:]
        self.target_values = list_in[312:624]
        print('[+] Filtering possible state candidates.')
        for index, target in enumerate(self.target_values):
            # index of corresponding state values since 1 dbl ~ 2 state values
            """For each Target 2 new state values influence the target double value. 
            the first new state value is dependent on a,b and x
            the second new state value is dependent on b,c and y
            according to the iterative twisting algorithm"""
            index_a = index*2
            index_b = index_a + 1
            index_c = index_a + 2
            index_x = index_a + self.m
            index_y = index_b + self.m
            # get corresponding tempered values, set the number of variant bits for each
            a, b = self.split_ab(self.base_values[index])
            varb_a, varb_b = 5, 6
            c, _ = self.split_ab(self.base_values[index + 1])
            varb_c = 5
            # TODO reference index of x,y base values directly and not via state index
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
            cands_a, cands_b, cands_x = self.verify_candidates(cands_a, cands_b, cands_x, target, False)
            self.update_candidates(index_a, cands_a)
            self.update_candidates(index_b, cands_b)
            self.update_candidates(index_x, cands_x)

            # Attack 2nd state Value (c+y)
            cands_b, cands_c, cands_y = self.verify_candidates(cands_b, cands_c, cands_y, target, True)
            self.update_candidates(index_b, cands_b)
            self.update_candidates(index_c, cands_c)
            self.update_candidates(index_y, cands_y)
            print(f'[+] Progress: [{index+1}/{len(self.target_values)}] targets evaluated.', end='\r')
        self.untemper_candidates()
        self.update_valid_states()
        print(f'\n[+] State calculation finished. Valid states: {self.valid_states}.')

    def reverse_state_double(self, values, repeat=False):
        self.build_cands_dbl(values)
        self.build_state()
        if not repeat:
            self.sync_state(values[-50:])

def timetrail(reps = 20):
    from time import time
    from statistics import mean
    import random
    times = []
    for _ in range(reps):
        seed = random.getrandbits(32)
        gen = MT32Dbl()
        refgen = random.Random(seed)
        doubles = [refgen.random() for _ in range(624)]
        begin = time()
        gen.build_cands_dbl(doubles)
        times.append(time()-begin)
    print(times)
    print("Average: ", mean(times))

def test_vs_python_random(tests = 5):
    from random import Random
    gen = MT32Dbl()
    refgen = Random()
    doubles = [refgen.random() for _ in range(624)]
    gen.reverse_state_double(doubles)
    for i in range(tests):
        cloned = gen.get_double()
        orig = refgen.random()
        print(f"[+] cloned: {cloned}, original: {orig}, {cloned==orig}")
    #print(gen.valid_states)
    #return gen, refgen, doubles


if __name__ == '__main__':
    #import cProfile
    #cProfile.run(main())
    #gen, refgen, doubles = main()
    #for i in range(10):
    #    print(f'============Test number {i} ===========')
    #    test_vs_python_random()
    test_vs_python_random()