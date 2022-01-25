#%matplotlib inline
#import matplotlib.pyplot as plt
from pylab import *

figure(figsize=(6,6))
subplot(111, aspect='equal')
axis([0,9000,0,9000])
xlabel('bands')
ylabel('coils')

# 1 constraint
x = array([0,8000])
y = 140*(40 - (1/200)*x)
plot(x,y,'r',lw=2)
#fill_between([0,14],[14,0],color='r',alpha=0.15)


# 2 constraint
x = array([0,8000])
y = 4000 -x + x
plot(x,y,'b',lw=2)
#fill_between([0,14],[8,8],color='b',alpha=0.15)


# 3 constraint
y = array([0,8000])
x = 6000 - y + y
plot(x,y,'skyblue',lw=2)
#fill_between([5,14],[14,14],color='skyblue',alpha=0.15)

legend(['Constraint1','Constraint2','Constraint3'])

fill_between([0,2285,6000, 6000],[4000,4000,1400,0],color='b',alpha=0.15)

# Contours of constant profit
x = array([0,8000])
for i in linspace(-1000,1000,3):
    y = -25/30*x+6400-i
    plot(x,y,'y--')

# Optimum
plot(6000,1400,'r.',ms=20)
annotate('Solution', xy=(6000,1400), xytext=(200.0,200.0),
         arrowprops=dict(shrink=.1,width=1,headwidth=5))

savefig('prod.png', bbox_inches='tight')

show()

