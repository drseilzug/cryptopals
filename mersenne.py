class Mersenne(object):
    def __init__(self, seed=5489, w=32, mode=0):
        self.word = w
        self.set_params()

        self.lower_mask = (1 << self.r) - 1
        self.upper_mask = 1 << self.r

        self.initialize_from_seed(seed, mode)

    def initialize_from_seed(self, seed, mode=0):
        """ initialize generator from seed
        modes:
            0 :: reference implementation
            1 :: python implementation [EXPERIMENTAL]"""
        # TODO: figure out why this does not mimic the behaviour of pythons random.seed()
        self.state = [[] for _ in range(self.n)]
        self.index = self.n
        self.state[0] = seed
        if mode == 0:
            for i in range(1, self.n):
                pre_state = self.f * (self.state[i-1] ^ (self.state[i-1] >> (self.word - 2))) + i
                self.state[i] = self.cut(pre_state)  # cut off excess bits to have a 32/64 bit int
        elif mode == 1:
            raise NotImplementedError
        else:
            raise ValueError("Unknown mode Parameter supplied: {}".format(mode))

    def set_params(self):
        """initialized generator parameters according to the set wordsize. (32 or 64)"""
        if self.word == 32:
            # parameters (for w = 32)
            self.n = 624
            self.r = 31
            self.f = 1812433253
            self.a = 0x9908B0DF
            self.m = 397
            self.u = 11
            self.d = 0xFFFFFFFF
            self.s = 7
            self.b = 0x9D2C5680
            self.t = 15
            self.c = 0xEFC60000
            self.l = 18
        elif self.word == 64:
            # parameters (for w = 64)
            self.n = 312
            self.r = 31
            self.f = 6364136223846793005
            self.a = 0xB5026F5AA96619E9
            self.m = 156
            self.u = 29
            self.d = 0x5555555555555555
            self.s = 17
            self.b = 0x71D67FFFEDA60000
            self.t = 37
            self.c = 0xFFF7EEE000000000
            self.l = 43
        else:
            raise ValueError("w has to be 32 or 64")

    def set_state(self, state, index=0):
        """Sets an internal state for MT
        state: list of 624 32bit integers  (or 312 64 bit integers if w=64)
        index = where to begin inside the state"""
        if len(state) != self.n:
            raise ValueError("State must be a List of ints of length {}".format(self.n))
        else:
            self.state = state
            self.index = index

    def get_state(self):
        """Returns the internal state of the MT as a tuple (state, index)"""
        return self.state, self.index

    def reverse_state(self, values, repeat=False):
        """Rebuilds the state of a generator from 624 (312 for 64 bit version) consecutive
        values from another generator.
        If the repeat flag is set, it will replay the values it was reversed from. (default = False)
        """
        if len(values) < self.n:
            raise ValueError("Needs list of at least {} consecutive values to build state".format(self.n))
        values = values[-self.n:]  # reverses from the last 624 given output values.
        new_state = list(map(self.untemper, values))
        if repeat:
            self.set_state(new_state)
        else:
            self.set_state(new_state, self.n)  # sets up generator to twist on next call to sync with source gen

    def clone_from_function(self, func, repeat=False):
        """clones an MT generator by repeatedly calling its get_value function"""
        values = [func() for _ in range(self.n)]
        self.reverse_state(values, repeat)

    def clone_from_getrandbits(self, func, repeat=False):
        """Clones an MT generator by repeatedly calling a get_randbits(bitlength) function"""
        self.clone_from_function(lambda: func(self.word), repeat)

    def get_value(self):
        """returns a random value from the generator"""
        if self.index >= self.n:
            self.twist()
        # temper value
        ret_val = self.temper(self.state[self.index])
        self.index += 1
        return ret_val

    def temper(self, y):
        y ^= y >> self.u & self.d
        y ^= y << self.s & self.b
        y ^= y << self.t & self.c
        y ^= y >> self.l

        return self.cut(y)  # i think the cut here is unnecessary but not entirely sure

    # def _untemper(self, value):
    #     """old slow method to untemper"""
    #     def inv_ls(value, offset, d):
    #         """ value = y ^ (y << offset & d) ==> calculates y"""
    #         y = 0
    #         for i in range(self.word):
    #             y += (value ^ (y << offset & d)) & (1 << i)
    #         return y
    #
    #     def inv_rs(value, offset, d):
    #         """ value = y ^ (y >> offset & d) ==> calculates y"""
    #         y = 0
    #         for i in range(self.word-1, -1, -1):
    #             y += (value ^ (y >> offset & d)) & (1 << i)
    #         return y
    #     x = inv_rs(value, self.l, (1 << self.word) - 1)
    #     x = inv_ls(x, self.t, self.c)
    #     x = inv_ls(x, self.s, self.b)
    #     x = inv_rs(x, self.u, self.d)
    #     return x

    def untemper(self, value):
        """Inverse of the tempering function"""
        value ^= value >> self.l
        value ^= value << self.t & self.c
        for i in range(7):
             value ^= value << self.s & self.b
        for i in range(3):
             value ^= value >> self.u
        return value

    def get_values(self, n):
        """return a list of n {}bit values""".format(self.w)
        value_list = []
        for i in range(n):
            value_list.append(self.get_value())
        return value_list

    def twist(self):
        """generates a full state from the current self.state and resets self.index=0"""
        for i in range(self.n):
            x = self.state[i] & self.upper_mask
            x += self.state[(i+1) % self.n] & self.lower_mask
            xA = x >> 1
            if x % 2 != 0:
                xA ^= self.a
            self.state[i] = self.state[(i + self.m) % self.n] ^ xA
        self.index = 0

    def single_twist(self, v_624, v_623, v_227):
        """ helper function that builds a single state value out of
        the respective inputs needed for the recursion
        inputs are the values 624, 623 and 227 positions before the desired value in that states list (for 32 bit version)

        Returns it result and doesnt touch the internal state of the Object.

        Should work with 64 bit version too by using the respective input values according to the 64 bit versions parameters
        """
        x = v_624 & self.upper_mask
        x += v_623 & self.lower_mask
        xA = x >> 1
        if x % 2 != 0:
            xA ^= self.a
        res = v_227 ^ xA
        return res

    def cut(self, value):
        mask = (1 << self.word) - 1
        return value & mask

    def get_double(self):
        """ Uses up 2 output to get a double value mimicking what pythons
        Random module does"""
        a = self.get_value() >> 5
        b = self.get_value() >> 6
        return (a*67108864.0+b) * (1.0/9007199254740992.0)

    def getrandbits(self, k):
        """returns k random bits as an int"""
        wc = (k - 1) // self.word + 1
        wordlist = [[] for _ in range(wc)]
        while k > 0:
            value = self.get_value()
            if k < 32:
                value >>= self.word - k
            wordlist[wc - 1] = value
            k -= self.word
            wc -= 1
        out = 0
        for word in wordlist:
            out <<= self.word
            out += word
        return out


if __name__ == '__main__':
    import random
    import time

    def test_vs_rand_buildin_bits(n):
        #seed = int(time.time())
        gen = Mersenne()
        #random.seed(seed)
        gen.clone_from_getrandbits(random.getrandbits)
        g_bits = gen.getrandbits(n)
        r_bits = random.getrandbits(n)
        return g_bits == r_bits

    def test_vs_rand_buildin_dbl(n):
        #seed = int(time.time())
        gen = Mersenne()
        #random.seed(seed)
        gen.clone_from_getrandbits(random.getrandbits)
        g_dbl_list = [gen.get_double() for _ in range(n)]
        r_dbl_list = [random.random() for _ in range(n)]
        return g_dbl_list == r_dbl_list

    def test_vs_buildin_seeding(n):
        seed = int(time.time())
        gen = Mersenne(seed)
        random.seed(seed)
        return gen.getrandbits(n) == random.getrandbits(n)

    print("Testing getrandombits: ", test_vs_rand_buildin_bits(3223))
    print("Testing get_double: ", test_vs_rand_buildin_dbl(1000))
    print("Testing seeding: ", test_vs_buildin_seeding(32123))
