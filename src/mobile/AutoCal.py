from enum import Enum


class Direction(Enum):
    Left = 0;
    Right = 1;


def getWeight(m):
    return m*9.8;

def getTorque(m,d):
    return m*d;

def getDistance(targetMass, *others):
    sum = 0;
    for x in others:
        sum += x;
    distance = sum / targetMass
    return distance;


def sof(m1, m2, length, cut = 0.5,l1 = 0,l2 = 0):
    if(m1>m2):
        mass3 = m1
        mass1 = m2
    else:
        mass3 = m2
        mass1 = m1
        temp = l2
        l2 = l1
        l1 = temp

    mass2 = length * 0.45;
    l2/=2
    l1/=2
    shortlength = (mass1 * length - mass1 * 2 * cut + mass2 * 0.5 * length - mass2 * cut) / (mass1 + mass2 + mass3)
    longlength = length - shortlength - cut*2


    # print("coefficient durning calculation")
    # print("mass of dowel %f, torque of lighter obj %f,torque of dowel %f" % (mass2, mass1*(length-cut*2),(mass2*(length-cut*2)/2)))
    # print("coefficient of x is" + str( mass2 + mass1 + mass3))
    print("x = " + str(shortlength))
    # print("total mass %f" % (mass2 + mass1 + mass3 + 0.33))
    # print(ptable(mass3, shortlength)+ptable(mass2, ((length-cut*2)/2-shortlength))+ptable(mass1, (length-cut*2)-shortlength))
    print("20% Rule pass" if((longlength - shortlength)>length*0.2) else "Not Pass %.2f" % abs((longlength - shortlength-length*0.2)))
    sum = l1+l2+longlength+shortlength
    if(l1 != 0 or l2 != 0):
        print(f"{l2:.2f} {longlength:.2f} {shortlength:.2f} {l1:.2f}, Total{sum}")
    return mass2 + mass1 + mass3 + 0.33

def ptable(m1,d1):
    t1 = m1*d1/1000*9.8
    return f"{m1:.5f}\t{d1:.5f}\t{t1:.5f} "

def main():
    print("Tier 1")
    m1 = sof(12.8, 146.8, 13,l1 = 6, l2 = 15)
    print("Tier 2")
    m2 = sof(78.6,190.7,13,l1 = 11.5, l2 = 28)
    print("Tier 3")
    m3 = sof(m1,29.7,16, l1 = 22.5, l2 = 5)
    print("Tier 4")
    m4 = sof(m2,80.1,20,l1 = 31.74, l2 = 9)
    print("Tier 5")
    m5 = sof(m3,m4,40, l1 = 45.87, l2 = 28.75)


    Index = 0

    for x in range(5):
        with open("output.md", 'a') as output:
            output.write(f"# Tier {Index}\n")
            output.write("$Left Torque = Right Torque$\n")
            output.write("$x\cdot{mass3} = {mass2}\cdot({length}-x) +{mass1}")

if __name__ == "__main__":
    main()
