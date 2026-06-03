# CommonUppRoad
uppaal: a folder for storing uppaal models and shell files for verifyta the models.

generate_cr_scenarios.py: putting the trajectory of the ego vehicle into a scenario.

generate_uppaal_models.py: converting a scenario into things in uppaal model.

## Prerequisites
Python 3.10

CommonRoad-io

ffmpeg 1.4

imageio-2.37.0

Uppaal 5.1.10-beta5

## Troubleshooting
"MovieWriter ffmpeg unavailable". [Solution](https://stackoverflow.com/questions/60033397/moviewriter-ffmpeg-unavailable-trying-to-use-class-matplotlib-animation-pillo).

## Citation
```
@inproceedings{gu2024commonupproad,
  title={CommonUppRoad: A Framework of Formal Modelling, Verifying, Learning, and Visualisation of Autonomous Vehicles},
  author={Gu, Rong and Tan, Kaige and H{\o}eg-Petersen, Andreas Holck and Feng, Lei and Larsen, Kim Guldstrand},
  booktitle={International Symposium on Leveraging Applications of Formal Methods},
  pages={385--404},
  year={2024},
  organization={Springer}
}
```
