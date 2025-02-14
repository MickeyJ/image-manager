from setuptools import setup, find_packages
import platform

# Define base requirements
base_requirements = [
    "PyQt5>=5.15.0",
    "opencv-python>=4.5.0",
    "numpy>=1.19.0",
    "Pillow>=8.0.0",
    "imagehash>=4.2.0",
    "scikit-learn>=0.24.0",
]

# Add platform-specific requirements
if platform.system() == "Windows":
    torch_requirement = [
        "torch>=2.0.0",  # Will be overridden by requirements_windows.txt
        "torchvision>=0.15.0",
    ]
else:
    torch_requirement = ["torch>=2.0.0", "torchvision>=0.15.0"]

# Combine requirements
install_requires = (
    base_requirements
    + torch_requirement
    + ["clip @ git+https://github.com/openai/CLIP.git"]
)

setup(
    name="image-manager",
    version="0.1.0",
    packages=find_packages(),
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "image-manager=main:main",
        ],
    },
    author="Your Name",
    author_email="mickeyjmalotte@gmail.com",
    description="An AI-powered image management tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mickeyj/image-manager",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.8",
)
