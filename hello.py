

def hello():
    print('this is a hello')
    print("--------")
    print('this  is a world!')


class People:

    def __init__(self, name: str) -> None:
        self.name = name

    def say(self, name: str) -> None:
        print(f"{name},Hello,I am Bot")
        print("{name}")

    def jhh(self, age: int) -> int:

        return age


if __name__ == '__main__':
    p = People("Alice")
    p.say(name="JB")
    p.say(name="Gab")
