import matplotlib.pyplot as plt

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(m.nHrs, m.hInc, marker='o')
plt.title('Flows Over Time')
plt.xlabel('Time')
plt.ylabel('Fuel cell in')
plt.xticks(rotation=45)
plt.tight_layout()
ptl.show()

