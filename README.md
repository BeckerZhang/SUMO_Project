# _SUMO_Project--交通政策决策支持系统设计及目的：_
This is the code I wrote in the first year of my master's degree. It shows a secondary development simulation decision support system based on SUMO simulation. Any government officials and planners can evaluate 
traffic operation level and land use level by adjusting policies

## _**Auxiliary support decision algorithms**_

1. Based on the **_xxx_** city traffic big data

2. Through the construction of **_xxx_** urban traffic model

3. To achieve complete data analysis, decision-making aid closed loop

## _The procedure to run a transport decision-making process._

**First**, the main file is auto.py, and the input file is under the "\tw_rdc_case\in.." (you can choose any module you want to evaluate by changing the button from on to off)

**Second**, in the initial folder, python files are laid out in parallel, with different policy decision support evaluators modified by calling the same underlying logic. The expansibility and small modularity of 

the project are guaranteed.

**Third**, in the "\tw_rdc_case\cache.." folder, I saved some ".csv" files and ".xml" files which are necessary to guarantee the original logic of transportation simulation processing.

**Last**, after operating the auto.py file, it will create the new files in the "\tw_rdc_case.." including files called "output_xxx" and file called "output": 

**where**， "output_xxx" files include the operating files(.xml files) necessary for the simulation software; "output" file include the result of simulation evaluation system and the converted ".csv" files from 
".xml" files


## 📌 Citation

If you use this code in your research, please cite it as:

Zhang, Y. (2025). *Code for EV Charging Station Optimization (v1.0)* [Software]. Figshare. https://doi.org/10.6084/m9.figshare.12345678

[![DOI](https://zenodo.org/badge/DOI/10.6084/m9.figshare.12345678.svg)](https://doi.org/10.6084/m9.figshare.12345678)
