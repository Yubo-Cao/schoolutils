import SketchDrawer
import os, shutil

global Index
Index = 1

def sof(m1, m2, length, cut=0.5, l1=0, l2=0):
    global Index
    if (m1 > m2):
        mass3 = m1
        mass1 = m2
    else:
        mass3 = m2
        mass1 = m1
        temp = l2
        l2 = l1
        l1 = temp

    mass2 = length * 0.45
    l2 /= 2
    l1 /= 2
    shortlength = (mass1 * length - mass1 * 2 * cut + mass2 * 0.5 * length - mass2 * cut) / (mass1 + mass2 + mass3)
    longlength = length - shortlength - cut * 2

    # Output Sentences
    # print("coefficient durning calculation")
    # print("mass of dowel %f, torque of lighter obj %f,torque of dowel %f" % (mass2, mass1*(length-cut*2),(mass2*(length-cut*2)/2)))
    # print("coefficient of x is" + str( mass2 + mass1 + mass3))
    # print("x = " + str(shortlength))
    # print("total mass %f" % (mass2 + mass1 + mass3 + 0.33))
    # print(ptable(mass3, shortlength)+ptable(mass2, ((length-cut*2)/2-shortlength))+ptable(mass1, (length-cut*2)-shortlength))
    # print("20% Rule pass" if ((longlength - shortlength) > length * 0.2) else "Not Pass %.2f" % abs(
    #     (longlength - shortlength - length * 0.2)))
    # sum = l1 + l2 + longlength + shortlength
    # if (l1 != 0 or l2 != 0):
    #     print(f"{l2:.2f} {longlength:.2f} {shortlength:.2f} {l1:.2f}, Total{sum}")

    # Temp Coefficient For Formatting
    length2 = length / 2 - cut
    length3 = length - cut * 2
    length4 = length * 0.2
    length5 = longlength - shortlength
    sumcoefficient1 = mass1 + mass2 + mass3
    sumcoefficient2 = length2 * mass2 + length3 * mass3
    Path = f'Tier{Index}.png'

    SketchDrawer.generateGraph(mass1, mass2, mass3, length, Path)

    with open("output.md", 'a') as output:
        output.write(f"# Tier {Index}\n\n")
        output.write(f"![Tier{Index}]({Path})\n\n")
        output.write(f"$Left\;Torque = Right\;Torque$\n\n")
        output.write(f"$x\cdot{mass3:.2f} = {mass2:.2f}\cdot({length2:.2f}-x) +{mass1:.2f}\cdot({length3:.2f}-x)$\n\n")
        output.write(f"$x\cdot{sumcoefficient1:.2f} = x\cdot{sumcoefficient2:.2f}$\n\n")
        output.write(f"$x = \\boxed{{{shortlength:.2f}cm}}$\n\n")
        output.write("\n\n")
        output.write(f"Short length $\\boxed{{{shortlength:.2f}cm}}$\n\n")
        output.write(f"Long length ${length3:.2f}cm - {shortlength:.2f}cm = \\boxed{{{longlength:.2f}cm}}$\n\n")
        output.write("\n\n")
        output.write("20% Rule Check\n\n")
        output.write(f"$20%\\times{length:.2f}cm = {length4:.2f}cm$\n\n")
        output.write(f"${longlength:.2f}cm - {shortlength:.2f}cm = {length5:.2f}cm$\n\n")
        output.write(f"${length5:.2f}cm>{length4:.2f}cm$ Good to Go!\n\n")
        output.write("\n\n")

    with open("header.md", 'a') as output:
        output.write("|" + f"Tier{Index}" + "|" + "|".join(
            ptable(mass3, shortlength) + ptable(mass1, longlength) + ptable(mass2, length2 - shortlength)) + "|")
        output.write("\n")

    Index += 1
    return mass2 + mass1 + mass3 + 0.33


def ptable(m1, d1):
    m1 /= 1000
    t1 = m1 * d1 * 9.8
    return f"{m1:.3f}", f"{d1:.3f}", f"{t1:.4f}"

def Initialization():
    ## Delete some Trash, result from last time running
    PWD = os.path.abspath('.')
    try:
        os.remove('output.md')
    except:
        pass
    try:
        os.remove('header.md')
    except:
        pass
    try:
        os.rmdir(os.path.join(PWD,'output'))
    except:
        pass
    
    os.mkdir(os.path.join(PWD,'output'))
    
    for x in range(1,6):
        os.remove(f'Tier{x}.png')

    with open("header.md", 'a') as output:
        output.write(
            "|  | mass1($kg$) | distance1($cm$) | Torque1($N\cdot cm$) | mass2(optional)($kg$) | distance2(optional)($cm$) | Torque2(optional)($N\cdot cm$) | mass of dowel($kg$) | distance to center of dowel($cm$) | Torque produced by dowel($N\cdot cm$) |\n")
        output.write("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")

    SketchDrawer.generateGraph(10,10,10,10,'Test.png')
    os.remove('Test.png')

Initialization()

print("Tier 1")
m1 = sof(12.8, 146.8, 13, l1=6, l2=15)
print("Tier 2")
m2 = sof(78.6, 190.7, 13, l1=11.5, l2=28)
print("Tier 3")
m3 = sof(m1, 29.7, 16, l1=22.5, l2=5)
print("Tier 4")
m4 = sof(m2, 80.1, 22, l1=31.74, l2=9)
print("Tier 5")
m5 = sof(m3, m4, 36, l1=45.87, l2=28.75)


