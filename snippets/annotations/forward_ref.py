"""A forward reference in an annotation: Python 3.14 against 3.12."""


class Master:
    def attach(self) -> Slave:  # noqa: F821  Slave is defined below
        return Slave()


class Slave:
    pass


print("annotation:", Master.attach.__annotations__)
