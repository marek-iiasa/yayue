#%matplotlib inline
#import matplotlib.pyplot as plt
from pylab import *

figure(figsize=(6,6))
subplot(111, aspect='equal')
axis([0,15,0,15])
xlabel('p')
ylabel('w')

# 1 constraint
x = array([0,14])
y = 14 - x
plot(x,y,'r',lw=2)
#fill_between([0,14],[14,0],color='r',alpha=0.15)


# 2 constraint
x = array([0,14])
y = 8 -x + x
plot(x,y,'b',lw=2)
#fill_between([0,14],[8,8],color='b',alpha=0.15)

# 3 constraint
y = array([0,14])
x = 5 - y + y
plot(x,y,'skyblue',lw=2)
#fill_between([5,14],[14,14],color='skyblue',alpha=0.15)

legend(['Constraint1','Constraint2','Constraint3'])

fill_between([5,6,14],[8,8,0],color='b',alpha=0.15)

# Contours of constant profit
x = array([0,14])
for i in linspace(-3,3,7):
    y = -1/5*x+(8+6/5)+i
    plot(x,y,'y--')

# Optimum
plot(6,8,'r.',ms=20)
annotate('Solution', xy=(6,8), xytext=(0.5,0.5),
         arrowprops=dict(shrink=.1,width=1,headwidth=5))

savefig('first1.png', bbox_inches='tight')
show()

