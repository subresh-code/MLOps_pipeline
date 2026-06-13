CMP6230 Coursework Task Sheet 2

Data Analytics Pipeline: Implementation and Deployment

Your second task will be to **implement** a **data management** and **data analytics** strategy based on the previously identified datasource(s) investigated during task 1, this will involve the production of a MLOps pipeline intended to **automate** the **ingestion** of said data for the **production** of Machine Learning models. This will be documented within your log report.

The purpose of this task is to contribute towards meeting the module learning outcome: “**Implement** an **appropriate structure** for the **storage**, **retrieval** and **analytical processing** of data using **appropriate software**”

Underlined are some of the key parts of the learning outcome, but what do they mean?

* Implement

  * You will be expected to provide detailed **evidence** of the development, setup and configuration process of your Machine Learning Operations pipeline

* Appropriate structure

  * Your pipeline and data storage system should be well justified based on the iterative refinements made to your previous plans and designs

* Storage

  * The pipeline development process needs to consider not only how the data will be stored, but how it will be used, this should also be communicated appropriately.

  * Once the data has been ingested it should be stored using appropriate tools and techniques (for instance, in our lab discussions we have used tools such as Column-oriented datastores and Key-Value data stores)

* Retrieval

  * The pipeline development process needs to consider not only how the data will be ingested, but also how it will be accessed for later use, either for the purposes of

    developing the Machine Learning model itself or for the purposes of more specific investigations into the data by the Data Science / Data Engineering team.

* Analytical Processing

  * The modelling process must also consider that the stored data will be used to develop Machine Learning models and apply various analytics techniques. These

    considerations must also be communicated to the reader.

  * The majority of the later stages of the pipeline will be based around automating the production of Machine Learning models in a manner suitable for later deployment into a given system

* Appropriate software

  * Each technique leveraged within each pipeline stage should be supported by software. Each piece of software used should have its purpose within the pipeline clearly defined (what benefits does it provide?)

|  Note |
| :---- |
| The information contained within this document may be subject to further change to provide further clarification of aspects of the coursework, or to provide additional advice/guidance for the task. |

# **What you need to do**

## **Exercise 2: Step 1**

**Produce an** appropriate Data Analytics / Machine Learning Operations pipeline for the storage and processing of data from one or more data sources to automate the production of Machine Learning models.

This section of the log report should include a detailed discussion of the following **development** stages of the data analytics pipeline:

* Data Ingestion

  * e.g., how does your pipeline consume data from one or more data sources and then store it for later retrieval?

    * Have you used?

      * ETL

      * ELT

* Data Pre-processing

  * e.g., how does your pipeline transform the data further, to allow for more effective usage by Machine Learning algorithms

* Model Development

  * e.g., how does your pipeline use the transformed data to train / fit an appropriate Machine Learning model?

* Model Deployment

  * e.g., how are the resulting model versions stored for later retrieval? (hint: serialisation?)

  * e.g., how might the stored models be accessible not only on a local machine, but also via a network? (hint: containers, like docker?)

* Model Monitoring

  * e.g., how can the models performance be checked once it is deployed?

For each stage, you should aim to discuss:

* The What

  * What is the stage being undertaken?  
    * e.g., what does “data ingestion” actually mean?

  * What are the key components, systems and concepts that make up this stage?  
    * e.g., what tools and did you use for the data ingestion process?

  * What are the input dependencies to this stage?  
    * e.g., the data ingestion stage will likely require data

- How has the data been passed into this stage of the pipeline?

- Were there any requirements as to how that data needs to be represented/structured as input? If so, why?

  * What are the expected outputs of this stage?  
    * e.g., once the data ingestion stage is completed, what will the later stages actually “get” out of this stage?

* The Why

  * Why is this stage important?  
* e.g. why was the data pre-processing stage needed?  
  * Why are the key components, systems and concepts that make up this stage important?  
* e.g. what does each tool or technique contribute to the task being undertaken?

* The How

  * How was the stage implemented?

|  Tip |
| :---- |
| The design and development process of real-world systems are often iterative, this means that you are likely to benefit from refining your process throughout the development lifecycle. Therefore, this task should not be seen as a static “tick-box” document, instead, it should be reviewed throughout your progress with the module assessment and iteratively refined as you gain a better understanding of how to appropriately tackle the problem. Importantly, later more refined versions of your plan can then be compared against earlier versions |

### **Marking**

Marks will be awarded within this task based on:

* **Successful implementation** of an **appropriately documented** and **well-evidenced data analytics pipeline** accompanied by a sufficiently **detailed discussion** of the **development**, **setup,** and **configuration** process for said pipeline.

* A **reflective discussion** of the planning process undertaken including:

  * How does your current pipeline compare to your initial plans?  
  * How does your current pipeline compare to your final plan?  
    * Are there any discrepancies, if so, why?  
  * How would you improve upon the structure of the pipeline in the future?