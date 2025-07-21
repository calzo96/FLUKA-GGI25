#%%
import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
plt.rc('text', usetex=True)
plt.rc('font', family='serif')
# The tics shouls be inside the plot for both x and y
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
# Add subtics like root
plt.rcParams['xtick.minor.visible'] = True
plt.rcParams['ytick.minor.visible'] = True
# The grid should be dashed and grey and on by default
plt.rcParams['grid.color'] = 'grey'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.linewidth'] = 1
plt.rcParams['grid.alpha'] = 0.5

def get_all_detectors(path):
    with open(path, 'r') as file:
        lines = file.readlines()

    detectors = {} # Detector number and name
    # The line structure is: "Detector n: <number> <name> (integrated over solid angle)"
    for line in lines:
        match = re.search(r'Detector n:\s*(\d+)', line)
        if match:
            detector_number = int(match.group(1))
            detector_name = line.split()[4]
            detectors[detector_name] = detector_number
    return detectors

def get_df(path, detector_number=1):
    with open(path, 'r') as file:
        lines = file.readlines()

    # Find the line that contains the detector number
    detector_line = None
    for line in lines:
        match = re.search(rf'Detector n:\s*{detector_number}\b', line)
        if match:
            detector_line = line
            break

    # Read the next lines until the line is empty or just whitespace
    data_lines = []
    if detector_line:
        index = lines.index(detector_line) + 2
        while index < len(lines) and lines[index].strip():
            data_lines.append(lines[index].strip())
            index += 1

    # Create a DataFrame from the data lines
    data = []
    for line in data_lines:
        parts = line.split()
        if len(parts) >= 3:
            E_min = float(parts[0])
            E_max = float(parts[1])
            counts = float(parts[2])
            abs_error = float(parts[3])/100*counts
            data.append({'E_min': E_min, 'E_max': E_max, 'counts': counts, 'abs_error': abs_error})

    df = pd.DataFrame(data)
    return df

def get_yield(path, detector_number=1):
    df = get_df(path, detector_number)
    df_yield = df['counts'] * (df['E_max'] - df['E_min'])
    df_errors = df['abs_error'] * (df['E_max'] - df['E_min'])
    tot_yield = df_yield.sum()
    tot_abs_error = np.sum(df_errors**2)**0.5

    return tot_yield, tot_abs_error

class Simulation:
   def __init__(self, name, path):
        self.name = name
        self.path = path

        self.detectors = get_all_detectors(path)
        self.yields = {}
        for detector_name, detector_number in self.detectors.items():
            yield_value, abs_error = get_yield(path, detector_number)
            self.yields[detector_name] = {
                'yield': yield_value,
                'abs_error': abs_error
            }


test_simulation = Simulation("440GeV", "../runs/440GeV_21_tab.lis")
detectors = test_simulation.detectors
yields = test_simulation.yields


# I want to create an histogram of the yields for each detector
# The pattern is ../runs_loop_energy/<energy>_21_tab.lis
# And the energy under consideration is 10 20 50 100 200
energies = [10, 20, 50, 100, 200]
detector_names = list(detectors.keys())
labels = {'kp' : r'$K^+$', 'km' : r'$K^-$', 'pip' : r'$\pi^+$', 'pim' : r'$\pi^-$'}
yields_data = {name: [] for name in detector_names}
for energy in energies:
    path = f"../runs_loop_energy/{energy}_21_tab.lis"
    sim = Simulation(f"{energy}GeV", path)
    for name in detector_names:
        yields_data[name].append(sim.yields[name]['yield'])

# Now we can plot the yields for each detector
fig, ax = plt.subplots(figsize=(5, 3))
for i, name in enumerate(detector_names):
    energies = np.array(energies)
    y_values = np.array(yields_data[name])
    ax.plot(energies, y_values / energies, marker='o', label=labels[name])
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('Energy (GeV)')
ax.set_ylabel('Yield [N/pr/GeV]')
ax.set_title('Kaon and Pion Yields per Proton per GeV')
ax.legend(loc='center left', fontsize='small')
ax.grid(True, which='both', linestyle='--', linewidth=0.5)
fig.savefig('yields_per_proton_per_GeV.png', dpi=300, bbox_inches='tight')
plt.show()


