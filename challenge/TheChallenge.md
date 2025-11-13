# Insights: Data Engineering Challenge

## Background

As a leading digital note-taking app, has accumulated vast amounts of user interaction data. As a Senior Data Engineer, your task is to design and implement a highly optimized Spark-based system to process and analyze this data, deriving valuable insights about user behavior and app performance.

## Dataset

You are provided with two large datasets:

1. User Interactions (~ 1 TB, partitioned by date)
   - Schema: `(user_id: String, timestamp: Timestamp, action_type: String, page_id: String, duration_ms: Long, app_version: String)`
   - Example: `("u123", "2023-07-01 14:30:15", "page_view", "p456", 12000, "5.7.3")`

2. User Metadata (~ 100 GB, partitioned by country)
   - Schema: `(user_id: String, join_date: Date, country: String, device_type: String, subscription_type: String)`
   - Example: `("u123", "2022-01-15", "US", "iPad", "premium")`

Code to generate dataset:

```py
import csv
import random
from datetime import datetime, timedelta

def generate_user_id():
    return f"u{random.randint(1, 1000000):06d}"

def generate_timestamp():
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    return start_date + timedelta(seconds=random.randint(0, int((end_date - start_date).total_seconds())))

def generate_action_type():
    return random.choice(['page_view', 'edit', 'create', 'delete', 'share'])

def generate_page_id():
    return f"p{random.randint(1, 1000000):06d}"

def generate_duration_ms():
    return random.randint(100, 300000)

def generate_app_version():
    major = random.randint(5, 7)
    minor = random.randint(0, 9)
    patch = random.randint(0, 9)
    return f"{major}.{minor}.{patch}"

def generate_join_date():
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2023, 12, 31)
    return start_date + timedelta(days=random.randint(0, (end_date - start_date).days))

def generate_country():
    return random.choice(['US', 'UK', 'CA', 'AU', 'DE', 'FR', 'JP', 'IN', 'BR', 'MX'])

def generate_device_type():
    return random.choice(['iPhone', 'iPad', 'Android Phone', 'Android Tablet', 'Windows', 'Mac'])

def generate_subscription_type():
    return random.choice(['free', 'basic', 'premium', 'enterprise'])

def generate_user_interactions(num_records, filename):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['user_id', 'timestamp', 'action_type', 'page_id', 'duration_ms', 'app_version'])
        for _ in range(num_records):
            writer.writerow([
                generate_user_id(),
                generate_timestamp().strftime("%Y-%m-%d %H:%M:%S"),
                generate_action_type(),
                generate_page_id(),
                generate_duration_ms(),
                generate_app_version()
            ])

def generate_user_metadata(num_records, filename):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['user_id', 'join_date', 'country', 'device_type', 'subscription_type'])
        for _ in range(num_records):
            writer.writerow([
                generate_user_id(),
                generate_join_date().strftime("%Y-%m-%d"),
                generate_country(),
                generate_device_type(),
                generate_subscription_type()
            ])

# Generate sample datasets
generate_user_interactions(1000000, 'user_interactions_sample.csv')
generate_user_metadata(100000, 'user_metadata_sample.csv')

print("Sample datasets generated successfully.")
```

## Tasks

1. Data Processing and Optimization

   a. Implement a Spark job to join the User Interactions and User Metadata datasets efficiently, handling data skew.
      - Explain your approach to mitigate skew in the join operation, considering the potential for certain user_ids to be significantly more frequent.
      - Implement and justify your choice of join strategy (e.g., broadcast join, shuffle hash join, sort merge join).
   b. Optimize the job to minimize shuffle and avoid out-of-memory errors.
      - Implement techniques such as salting or custom partitioning to distribute data evenly.
      - Explain how you would adjust the level of parallelism for optimal performance.
   c. Implement appropriate partitioning and caching strategies.
      - Decide on a partitioning scheme for both input and output data, justifying your choice.
      - Implement and explain your caching strategy, including which DataFrames to cache and at what point in the execution plan.

2. User Engagement Analysis

   a. Calculate daily active users (DAU) and monthly active users (MAU) for the past year.
      - Define clear criteria for what constitutes an "active" user.
   b. Identify the top 1% (or X%) of power users based on total interaction time.
      - Explain how you handle outliers and extremely long duration values.
      - Implement a solution that scales efficiently for large datasets.
   c. Analyze user retention rates on a cohort basis (weekly cohorts for the past 6 months).
      - Define the cohort and retention criteria clearly.
      - Explain how you would visualize this data for easy interpretation.

3. Performance Metrics

   a. Calculate the 95th percentile of page load times for each app version.
      - Explain your approach to handling the potentially large number of distinct app versions.
      - Implement a solution that can handle updates to this metric in near real-time.
   b. Identify any correlation between device type and app performance.
      - Explain your choice of correlation metric and why it's appropriate for this analysis.
      - Discuss how you would visualize this correlation for non-technical stakeholders.
   c. Detect and analyze any anomalies in app usage patterns.
      - Define clear criteria for what constitutes an "anomaly" in this context.
      - Implement a method to automatically detect and report these anomalies.

4. Advanced Analytics

   a. Implement a session-based analysis to understand user behavior patterns: Calculate and analyze metrics such as session duration, actions per session, and session frequency.

5. Spark UI Analysis

   a. Analyze the Spark UI for your jobs and identify bottlenecks.
      - Provide a detailed walkthrough (using screenshots or a screen recording with loom.com) of your analysis process.
      - Identify at least three specific areas for potential optimization based on the Spark UI data.
   b. Explain key areas for optimization.
      - For each identified bottleneck, provide a hypothesis about its cause and a proposed solution.
      - Discuss how you would validate the impact of your proposed optimizations.
   c. Implement improvements based on your Spark UI analysis.
      - Choose one of your proposed optimizations and implement it.
      - Provide before and after comparisons of relevant Spark UI metrics to demonstrate the improvement.

6. Optimization and Monitoring [Optional - Explain]

   a. Implement custom accumulators to track key metrics during job execution.
      - Define at least three custom accumulators that provide insights into job progress and data quality.
      - Explain how these accumulators can be used for real-time monitoring and alerting.
   b. Implement any optimizations you will perform and explain them in detail why these optimizations are required


## Requirements

1. Use Spark 3.x with Scala or PySpark.
2. Implement the solution using best practices for production-grade code.
3. Write unit tests for your key functions.
4. Provide a comprehensive README with setup instructions and explanations of your approach.
5. Include comments in your code explaining complex logic and optimization techniques.
6. Provide a system architecture diagram explaining how your solution would be deployed in a production environment.
7. Include a section on data quality checks and error handling in your implementation.
8. Discuss how you would schedule and orchestrate these jobs in a production setting.

## Deliverables

1. Source code for all implemented Spark jobs.
2. A detailed report (markdown format) covering:
   - Your approach to each task
   - Optimization techniques used
   - Analysis of results
   - Spark UI screenshots with explanations
   - Challenges faced and how you overcame them
3. Unit tests for key components of your solution.
4. A requirements.txt or build.sbt file listing all dependencies.
5. A system architecture diagram and explanation of the production deployment strategy.

## Evaluation Criteria

1. Correctness and completeness of the implemented solutions.
2. Efficiency and scalability of the Spark jobs.
3. Code quality, readability, and adherence to best practices.
4. Depth of analysis and insights derived from the data.
5. Appropriate use of Spark features and optimization techniques.
6. Quality of explanations

## Time Estimate

This challenge is designed to take approximately 3 to 6 hours for an experienced Spark developer. However, feel free to spend additional time if you wish to explore more advanced optimizations or analyses.

## Submission

Please submit your solution as a Git repository with all the required files and documentation. Ensure that your repo includes a clear history of commits showing your development process.

Good luck!