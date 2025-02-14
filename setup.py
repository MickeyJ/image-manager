from setuptools import setup, find_packages

setup(
    name="image-manager",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15.0",
        "opencv-python>=4.5.0",
        "numpy>=1.19.0",
        "Pillow>=8.0.0",
        "torch>=1.7.0",
        "clip @ git+https://github.com/openai/CLIP.git",
        "imagehash>=4.2.0",
        "scikit-learn>=0.24.0",
    ],
    entry_points={
        "console_scripts": [
            "image-manager=main:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="An AI-powered image management tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/image-manager",
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
