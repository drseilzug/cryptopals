from mersenne import Mersenne
import time
import random


def get_seed():
    pre_time = random.randint(40, 500)
    post_time = random.randint(0, 200)
    time.sleep(pre_time)
    seed = int(time.time())
    time.sleep(post_time)
    MT = Mersenne(seed)
    return MT.get_values(5)


def main():
    start = int(time.time())
    print("starting")
    out = get_seed()
    print("done")
    end = int(time.time())
    print("values: ", out)
    first = out[0]
    ans = None
    gen = Mersenne(start)
    for seed in range(start, end):
        gen.initialize_from_seed(seed)
        if gen.get_value() == first:
            ans = seed
            print("Found it!")
            break
    print(ans)


def main2():
    gen = Mersenne()
    for seed in range(0, 20):
        gen.initialize_from_seed(5)
        print(gen.get_value())


if __name__ == '__main__':
    main()
