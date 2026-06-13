  
CMP6230 Coursework Task Sheet 3

Data Analytics Pipeline: Application and Analysis

Your third task will be to **access** the **data which was ingested** previously during task 2 to attempt to answer a few questions, this will involve using some of the resulting outputs from the previously deployed MLOps pipeline and performing some **Exploratory Data Analysis** on this ingested data. This process will be documented within your log report.

The purpose of this task is to contribute towards meeting the module learning outcome: “Generate **insight** based on **organisational needs** by applying **appropriate tools** to **process and analyse stored data**”

Underlined are some of the key parts of the learning outcome, but what do they mean?

* Insight, Organisational needs

  * While we may not be discussing a formal "organisation" as such based on your chosen dataset(s), it is important to consider the useful information that can be gleaned by analysing your dataset and consider what **insights** your analysis provides about the nature of the data.

* Appropriate tools, Process and analyse.

  * You will need to access the data stored previously during the data ingestion phase of your pipeline.

    * This will require using the data storage systems previously used as a target for the data ingestion phase.

  * You will need to perform exploratory analysis of your data using appropriate data summarisation and visualisation techniques.

* Stored data

  * The data which will be targeted for this analysis process is the result of the data ingestion process initially described in task 1 and deployed in task 2

# **What you need to do**

## **Exercise 3: Step 1**

Explore and discuss your answers to the following questions based on your analysis of the previously ingested data which was stored during task 2\.

* What [statistical data type](https://en.wikipedia.org/wiki/Statistical_data_type)[/level of measurement](https://en.wikipedia.org/wiki/Level_of_measurement) adequately capture the nature of each variable of your data?

  * How might the kind of data change what kinds of analysis/visualisations are performed?

  * If you have not already done this for the stored data schema, do it during this stage otherwise you can link back in with elements of your previous discussion from task 1\.

* Formulate at least 3 data analysis-based **research questions** for your dataset.

* Additionally, answer the following for your dataset:

  * Are there any **outliers** or **missing values** within each of your data variables?

    * Why might this be?

      * Think about the context of your data.

        o e.g.

        * Is the outlier likely to be correct based on what you know about the data?

        * Could the outlier be an example of a data entry error?

  * What is the **distribution** of each variable within your dataset? What does this reveal about the **structure** of each data variable?

  * What **relationships** can be identified within your data?

    * What relationships can you identify between your different independent "feature" variables?

    * What relationships can you identify between each of your independent "feature" variables and the dependent "target" variable?

  * Are there any **differences** between the **ingested/stored data** and the **initial data source** used for ingestion? If so, why?

## **Exercise 3: Step 2 \- Research**

Explore and discuss your answers to the following questions based on your independent research into the following topics.

* What is **model drift** and how might it impact a **deployed, production Machine Learning** system?

  * What is **data drift**?  
  * What is **concept drift**?

* How might we combat **model drift** in a **deployed, production Machine Learning** system?

| ![][image1] Tip |
| :---- |
| The design and development process of real-world systems are often iterative, this means that you are likely to benefit from refining your process throughout the development lifecycle. Therefore, this task should not be seen as a static “tick-box” document, instead, it should be reviewed throughout your progress with the module assessment and iteratively refined as you gain a better understanding of how to appropriately tackle the problem. Importantly, later more refined versions of your plan can then be compared against earlier versions |

### **Marking**

Marks will be awarded within this task based on:

* **Successful processing and analysis** of the previously ingested data set(s) accompanied by a sufficiently **detailed discussion** of the analysis process used to gain further insight into the data.

* A **reflective discussion** of the planning and deployment process previously undertaken including:

  * How does your current pipeline effectively facilitate access to the ingested data by both people (Data Scientists, Data Engineers, Data Analysts) and software systems? (e.g. the pipeline)

  * How does your current pipeline compare to your initial plans?

  * How does your current pipeline compare to your final plan?

    * Are there any discrepancies, if so why?

  * How would you improve upon the structure of the pipeline in the future?

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAfCAYAAADwbH0HAAAB70lEQVR4XsWWQU4CQRBF6wgcwSMQT8AJYI5A4gVIvAA34AgkXmCWxogDC3ea4MJEFyQsXLBwMYlGjXFR8memQ1PV3dONMZC8QD7F/9Uz1T0QM9MxUEI0V9RVWgJKiOZowX9ECXxDY57RUOmHMqORy08XXlOPF/joMDmEgsrKU+i6MEROncqkoPmWZUN+yP1WgheEFrSuroYLNCF/E0AJTszlf+gxv0yY12Pm5yHzbUc3ELl6JSjMKjdTd5CLiNUrQWHMECwDQkifpGBsLWkYi2MLxQeHhqmNgqbKLyoYQwKD1ageJGkcg/TcCzZ7U25yM8mvOfNjpk1jgLf0bHJ2ouSSTpRRKtLTQgl74FSyjbD692W9n42GPf1T6qnHYEq/6GBMpm2GELwjCHsaDaAR05RdK29dUjCwzWCOQLzfd+vBA2ignO/q8GCQPsnB9uXGirFCvL7W9coBNDRg6vAolD7JwQDTKVdur9j+Tk6yByV4wfnbFtxyaNgoIUgoOOK+2iihwtf5gibe4Bllqh6X3XNmK6EyxxktdQBzXzAOHFlf+zmb0oUh6n8hJW8uvvnu9I2fzj54df4Z8/yVKCHEYDDobslcyNo2lBCiCR55iNpGBiWEaILHHv41OOv3+7mL7Xc9WR9CCTE0DUxBaqDhF1loY2PRnzd3AAAAAElFTkSuQmCC>