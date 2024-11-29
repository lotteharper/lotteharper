def generate_username(input):
    ONE = ['happy', 'sexy', 'fun', 'beautiful', 'pretty', 'handsome', 'dirty', 'gorgeous', 'stunning', 'lovely', 'perfect', 'busty', 'famous', 'best', 'lovely', 'stunning']
    TWO = ['person', 'woman', 'girl', 'beauty', 'sweetheart', 'lover', 'fox', 'bear', 'cutie', 'beast', 'babe', 'bestie', 'legend']
    from django.contrib.auth.models import User
    import random
    import sys
    TRIES = (len(ONE)-1) * (len(TWO)-1) * 100
    username = None
    tries = 0
    seed = ''
    for char in input:
        print(ord(char))
        seed = seed + str(ord(char))
    print(seed)
    random.seed(int(seed[:len(str(sys.maxsize))-1]) if seed else random.randrange(100000, 999999))
    while not username:
        username = ONE[random.randrange(0, len(ONE)-1)] + TWO[random.randrange(0, len(TWO)-1)] + str(random.randrange(0, 99))
        tries = tries + 1
        if tries > TRIES: break
        if User.objects.filter(username=username).count() == 0:
            return username
    return 'Guest' + str(random.randrange(100000, 999999))
