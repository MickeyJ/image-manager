import matplotlib.pyplot as plt

# Define the colors and their names
colors = {
    "Cerulean": "#007BA7",
    "Chartreuse": "#7FFF00",
    "Vermilion": "#E34234",
    "Periwinkle": "#CCCCFF",
    "Fuchsia": "#FF00FF",
    "Sienna": "#A0522D",
    "Indigo": "#4B0082",
    "Teal": "#008080",
    "Ochre": "#CC7722",
    "Mauve": "#E0B0FF",
}

# Create figure and axis
fig, ax = plt.subplots(figsize=(10, 5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 2)
ax.axis("off")

# Plot color splotches with names
for i, (name, hex_code) in enumerate(colors.items()):
    ax.add_patch(plt.Rectangle((i, 0.5), 1, 1, color=hex_code))  # Color splotch
    ax.text(
        i + 0.5, 1.7, name, ha="center", va="center", fontsize=12, weight="bold"
    )  # Label

# Save and display
plt.savefig("/mnt/data/color_splotches.png", dpi=300, bbox_inches="tight")
plt.show()
