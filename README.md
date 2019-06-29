# Statistical analysis of incident probability and causes on RATP metro lines

*Trafic perturbé*...again?! This library and this [notebook ](https://github.com/tianyikillua/ratpmetro/blob/master/examples/notebook.ipynb) provides a statistical point of view for all these daily incidents occurred on the Paris RATP metro lines.

<img width="450" src="https://user-images.githubusercontent.com/4027283/52844997-46dd8c00-3106-11e9-8e6d-3f812c8140c3.png">

Using tweets coming from official RATP Twitter accounts ([@Ligne1_RATP](https://twitter.com/Ligne1_RATP) for line 1 for example), we will see

1. What is the probability of encountering some operational incidents on a particular line?
2. Which lines are more likely to cause everybody unhappy?
3. What are the main causes of these problems?
4. Should I be considered lucky if I never take metros during rush hours?
5. Are there less problems during weekends?
6. Instead of going on vacation, is there any reason to be happy if I still work in August?

### Some examples in the year 2018

The fist two examples below refer to the RATP metro line 2, which I take everyday for work.

#### I should leave work before 17:00 on Wednesday (or after 21:00)

In the figure below you can see the probability of catching an operational incident (*trafic perturbé*, *interrompu*...) at a given hour (in fact in the next following hour) and a specific weekday. The maximum value (nearly 9%) can be found on Wednesday at the evening rush hours.

<img width="500" src="https://user-images.githubusercontent.com/4027283/52820966-c55a0f80-30ad-11e9-867d-c927fb74ca37.png">

#### It's us the main responsible for these incidents

Nearly half (48%) of the incidents come from us. Also, 9% is due to unattended bags...

<img width="450" src="https://user-images.githubusercontent.com/4027283/52821080-166a0380-30ae-11e9-8244-ad7e087cff89.png">

#### Line 13 should be jealous of line 4

Every Parisian knows that the line 13 is bad. But in the year 2018 it was beaten by the line 4, which records an average probability of incidents larger than 4%.

<img width="500" src="https://user-images.githubusercontent.com/4027283/52821104-2681e300-30ae-11e9-8ef3-7cb166656605.png">

### License

The code is licensed under the terms of the MIT license. The analysis results (text, figures, tables) are licensed under a [Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0/).

### Author

[Tianyi Li](https://www.linkedin.com/in/tianyikillua) ([tianyikillua@gmail.com](mailto:tianyikillua@gmail.com))
