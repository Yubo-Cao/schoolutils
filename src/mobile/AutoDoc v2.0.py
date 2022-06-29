import SketchDrawer
import os, shutil, tempfile

global Index
Index = 1
global header
header = open(tempfile.mkstemp(text=True)[1],'r+')
global body
body = open(tempfile.mkstemp(text=True)[1],'r+')

def sof(m1, m2, length, cut=0.5, l1=0, l2=0):
    global Index
    global body
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

    print("20% Rule pass" if ((longlength - shortlength) > length * 0.2) else "Not Pass %.2f" % abs(
        (longlength - shortlength - length * 0.2)))
    sum = l1 + l2 + longlength + shortlength
    if (l1 != 0 or l2 != 0):
        print(f"{l2:.2f} {longlength:.2f} {shortlength:.2f} {l1:.2f}, Total{sum}")

    # Temp Coefficient For Formatting
    length2 = length / 2 - cut
    length3 = length - cut * 2
    length4 = length * 0.2
    length5 = longlength - shortlength
    sumcoefficient1 = mass1 + mass2 + mass3
    sumcoefficient2 = length2 * mass2 + length3 * mass3
    Path = f'Tier{Index}.png'

    # Generate my Image
    SketchDrawer.generateGraph(mass1, mass2, mass3, length, Path)

    # Writing to Temp file
    body.write(f"# Tier {Index}\n\n")
    body.write(f"![Tier{Index}]({Path})\n\n")
    body.write(f"$Left\;Torque = Right\;Torque$\n\n")
    body.write(f"$x\cdot{mass3:.2f} = {mass2:.2f}\cdot({length2:.2f}-x) +{mass1:.2f}\cdot({length3:.2f}-x)$\n\n")
    body.write(f"$x\cdot{sumcoefficient1:.2f} = x\cdot{sumcoefficient2:.2f}$\n\n")
    body.write(f"$x = \\boxed{{{shortlength:.2f}cm}}$\n\n")
    body.write("\n\n")
    body.write(f"Short length $\\boxed{{{shortlength:.2f}cm}}$\n\n")
    body.write(f"Long length ${length3:.2f}cm - {shortlength:.2f}cm = \\boxed{{{longlength:.2f}cm}}$\n\n")
    body.write("\n\n")
    body.write("20% Rule Check\n\n")
    body.write(f"$20%\\times{length:.2f}cm = {length4:.2f}cm$\n\n")
    body.write(f"${longlength:.2f}cm - {shortlength:.2f}cm = {length5:.2f}cm$\n\n")
    body.write(f"${length5:.2f}cm>{length4:.2f}cm$ Good to Go!\n\n")
    body.write("\n\n")

    # Writing to Table file
    tableFormatter = lambda m,d : (f"{m:.3f}", f"{d:.3f}", f"{m*d:.4f}")
    header.write("|" + f"Tier{Index}" + "|" + "|".join(
        tableFormatter(mass3, shortlength) + tableFormatter(mass1, longlength) + tableFormatter(mass2, length2 - shortlength)) + "|")
    header.write("\n")

    Index += 1
    return mass2 + mass1 + mass3 + 0.33


## Delete some Trash, result from last time running
PWD = os.path.abspath('.')
for f in [x for x in os.scandir(PWD) if os.path.isfile(x) and( os.path.splitext(x)[1] == '.png')]:
    os.remove(f)

## Warm up of my SketchDrawer

SketchDrawer.generateGraph(10,10,10,10,'Test.png')
os.remove('Test.png')

## Output 1

try:
    shutil.rmtree(os.path.join(PWD,'Doc'))
except:
    print("First Time Running!")
finally:
    os.mkdir(os.path.join(PWD,'Doc'))


header.write("# Table\n\n")
header.write(
    "|  | mass1($kg$) | distance1($cm$) | Torque1($N\cdot cm$) | mass2(optional)($kg$) | distance2(optional)($cm$) | Torque2(optional)($N\cdot cm$) | mass of dowel($kg$) | distance to center of dowel($cm$) | Torque produced by dowel($N\cdot cm$) |\n")
header.write("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")



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

with open('Final.md','w') as output:
    with open('Header.md','r') as cust:
        output.write(cust.read())
        header.seek(0,0)
        output.write(header.read())
        body.seek(0,0)
        output.write(body.read())

header.flush()
body.flush()

for f in [x for x in os.scandir(os.path.abspath('.')) if os.path.isfile(x) and os.path.splitext(x)[1] == '.png']:
    shutil.move(os.path.abspath(f),os.path.join(PWD,'Doc'))

shutil.move('Final.md',os.path.join(os.path.abspath('.'),'Doc'))
        


