<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]

[![Data License][data-license-shield]][data-license-url]



<!-- PROJECT LOGO -->
<!-- <br />
<div align="center">
  <a href="https://github.com/othneildrew/Best-README-Template">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">Best-README-Template</h3>

  <p align="center">
    An awesome README template to jumpstart your projects!
    <br />
    <a href="https://github.com/othneildrew/Best-README-Template"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/othneildrew/Best-README-Template">View Demo</a>
    &middot;
    <a href="https://github.com/othneildrew/Best-README-Template/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/othneildrew/Best-README-Template/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div> -->



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#configurations">Configurations</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

This is the official repository for Vista-VID dataset.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Built With

* [Python][Python-url]
* [Gemini][Gemini-url]


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

Vista-VID is developed in Python, with usage of Gemini for creating data synthetic.

### Prerequisites

Make sure your system meets the following minimum requirements:

- **[Python](https://www.python.org/downloads/):** Version `3.12+`

### Tools

- **[`uv`](https://docs.astral.sh/uv/getting-started/installation/):**
    Simplify Python environment and dependency management. `uv` automatically creates a virtual environment in the root directory and installs all required packages for you—no need to manually install Python environments.

- **[`Gemini API`](https://ai.google.dev/)**
    LLM Provider from Google with many features for image, video understanding we built on  top of them.

### Installation

```sh

# Install dependencies, uv will take care of the python interpreter and venv creation, and install the required packages
uv sync

cp .env.example .env
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
### Configurations

Place the Gemini API Key in your .env file.

```
GOOGLE_API_KEY=YOUR_API_KEY
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

```python
uv run main.py
```

<!-- ROADMAP -->
## Roadmap

- [ ] Dataset:
    - [ ] Video Level-based Description Dataset
    - [ ] Video Captioning Dataset
    - [ ] Video QA Dataset

- [ ] Training recipes
- [ ] Benchmark
- [ ] Support other LLM providers

See the [open issues](https://github.com/hllj/Vista-VID/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Top contributors:

<a href="https://github.com/hllj/Vista-VID/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=hllj/Vista-VID" alt="contrib.rocks image" />
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the Unlicense License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Bui Van Hop - [@hopbui3](https://x.com/hopbui3) - vanhop3499@gmail.com

Project Link: [https://github.com/hllj/Vista-VID](https://github.com/hllj/Vista-VID)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

Vista-VID is built upon the incredible work of the open-source community. We are deeply grateful to all the projects and contributors whose efforts have made Vista-VID possible. Truly, we stand on the shoulders of giants.

We would like to extend our sincere appreciation to the following projects for their invaluable contributions:

* [Gemini Cookbook](https://github.com/google-gemini/cookbook)
* [LLaVA-Video](https://llava-vl.github.io/blog/2024-09-30-llava-video/)
* [InternVid](https://github.com/OpenGVLab/InternVideo/tree/main/Data/InternVid)


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/hllj/Vista-VID.svg?style=for-the-badge
[contributors-url]: https://github.com/hllj/Vista-VID/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/hllj/Vista-VID.svg?style=for-the-badge
[forks-url]: https://github.com/hllj/Vista-VID/network/members
[stars-shield]: https://img.shields.io/github/stars/hllj/Vista-VID.svg?style=for-the-badge
[stars-url]: https://github.com/hllj/Vista-VID/stargazers
[issues-shield]: https://img.shields.io/github/issues/hllj/Vista-VID.svg?style=for-the-badge
[issues-url]: https://github.com/hllj/Vista-VID/issues
[data-license-shield]: https://img.shields.io/badge/Data%20License-CC%20By%20NC%204.0-red.svg
[data-license-url]: https://img.shields.io/badge/Data%20License-CC%20By%20NC%204.0-red.svg

[Python-url]: https://www.python.org/
[Gemini-url]: https://gemini.google.com/