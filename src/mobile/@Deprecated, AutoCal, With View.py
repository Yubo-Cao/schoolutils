from enum import Enum


class Direction(Enum):
    Left = 0;
    Right = 1;


class CustType(Enum):
    Direction = 0;
    Weight = 1;
    Mass = 1;
    Distance = 2;
    Selection = 3;
    Boolean = 4;


class View:
    def __init__(self):
        print("This object is not expected to be initialize");
        raise Exception("This object is not expected to be initialize")

    @classmethod
    def menu(cls):
        print("1.Any number of hanging objects")
        print("2.Two objects + 1 Dowel, length of dowel")
        print("3.Current Torques")
        print("4.Add Torques")
        selection = View.read("What is your Selection", "Selection")
        if (selection == 1):
            print("What objects do you want to use?(Use number to select)")
            target = View.read("The hanging object that you only know mass", "Selection")
            others = [];
            while True:
                other = View.read("What are other hanging objects you will use on this dowel?(press -1 to exit)",
                                  "Selection")
                if (others == -1):
                    break;
                else:
                    others.append(other)

            others = map(lambda x:allTorque[x],others)

            print("The distance from fulcrum to this object should be:%.2f" % Control.getDistance(allTorque[target],*others))

        elif (selection == 2):
            m1 = View.read("What is object1","Selection");
            m2 = View.read("What is object2","Selection");
            mD = View.read("What is dowel","Selection");
            length = View.read("What is length of dowel?(cm)","Distance")
            cut = View.read("What is edge you want to leave for each side?(cm)","Distance")

            print("The fulcrum should be at:.2f" % Control.getFulcrum(allTorque[m1],allTorque[m2],allTorque[mD],length,cut))

        elif (selection == 3):
            for x in allTorque:
                print(str(allTorque[x]));

        elif (selection == 4):
            View.createTorque();

        else:
            print("Invalid Value")

    @classmethod
    def createTorque(cls):
        length = View.read("Distance from Fulcrum?(meter)", "Distance");
        mass = View.read("Mass or Weight from Fulcrum?(kg/N)", "Mass");
        isItWeight = View.read("weight?(True/False)", "Boolean")
        direction = View.read("Direction on the Fulcrum?(L/R)", "Direction");

        return model(length, mass, direction, isWeight=isItWeight);

    @classmethod
    def read(cls, name, type):
        while (True):
            x = input(f"What is {name}?");
            try:
                if (x == "" or x == "\n"):
                    return 0
                if (CustType[type] == CustType.Direction):
                    return View.parseDirection(x)
                elif (CustType[type] == CustType.Weight):
                    return float(x);
                elif (CustType[type] == CustType.Distance):
                    return float(x);
                elif (CustType[type] == CustType.Selection):
                    return int(x)
                elif (CustType[type] == CustType.Boolean):
                    if (x == "True"):
                        return True;
                    elif (x == "False"):
                        return False;
                    else:
                        raise Exception();
                break;
            except:
                View.raiseInputException(type)
                continue;
            break;

    @classmethod
    def parseDirection(cls, direction):
        if (direction == 'L'):
            direction = Direction.Left;
        elif (direction == 'R'):
            direction = Direction.Right;
        else:
            raise Exception("");
        return direction;

    @classmethod
    def raiseInputException(cls, x):
        print(f"The Input Value for {x} is invalid!")


class model:

    def __init__(self, distance, massOrWeight, direction=Direction.Left, *, isWeight=False):
        # 0 for left, 1 for right
        global index
        self.distance = distance;
        self.mass = massOrWeight / 9.8 if isWeight else massOrWeight
        self.direction = direction
        self.index = index;
        allTorque[index] = self;
        index += 1;

    def getTorque(self):
        return self.distance * self.massOrWeight

    def __str__(self):
        return f"[Torque Number {self.index} \t direction:{Direction(self.direction)},distance:{self.distance:.2f} m, mass:{self.mass:.3f} kg]"


class Control:
    def __init__(self):
        print("This object is not expected to be initialize");

    @classmethod
    def getDistance(cls, target, *others):
        if (target.direction == Direction.Left):
            sum = 0;
            for x in others:
                if (x.direction == Direction.Left):
                    sum -= x.getTorque();
                else:
                    sum += x.getTorque();
            target.distance = (sum - target.getTorque()) / target.distance
            return target.distane;
        else:
            sum = 0;
            for x in others:
                if (x.direction == Direction.Left):
                    sum += x.getTorque();
                else:
                    sum -= x.getTorque();
            target.distance = (sum + target.getTorque()) / target.distance
            return target.distance;

    @classmethod
    def getFulcrum(cls, m1, m2, mD, length, cut=0):
        mass3 = m1.mass if (m1.mass > m2.mass) else m2.mass;
        mass2 = mD.mass;
        mass1 = m2.mass if (m1.mass > m2.mass) else m1.mass;

        return (mass1 * length - mass1 * 2 * cut + mass2 * 0.5 * length - mass2 * cut) / (mass1 + mass2 + mass3);


# public static void main(String[] args){}

global index
index = 1
global allTorque
allTorque = {}

while (True):
    View.menu();
