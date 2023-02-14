import datetime

import requests
import pandas as pd
import matplotlib.pyplot as plt
from pandas import NaT


def main():
    """
    A script to generate a burn-down chart from a GitHub milestone
    Example usage: python3 main.py
    """

    # Prompt the user for the GitHub project
    project = input('Enter the GitHub project (e.g. nqsullivan/Burndown_Chart_Generator): ')

    # Prompt the user for the GitHub milestone
    milestone = input('Enter the GitHub milestone (e.g. 1): ')

    # Prompt the user for the GitHub username
    username = input('Enter the GitHub username: ')

    # Prompt the user for the GitHub personal access token
    pat = input('Enter the GitHub personal access token: ')

    # Pull the data from GitHub
    data = get_data(project, milestone, username, pat)

    # Get the milestone start date and end date from the api
    start_date, end_date = get_milestone_dates(project, milestone, username, pat)

    # Generate the burn-down chart
    # generate_burndown_chart(data, start_date, end_date)
    generate_burndown_chart(
        data,
        get_commits(project, start_date, end_date, username, pat),
        start_date,
        end_date
    )


def get_data(project, milestone, username, pat):
    """
    Pull the data from GitHub
    :param project: The GitHub project name
    :param milestone: The GitHub milestone number
    :param username: The GitHub username
    :param pat: The GitHub personal access token
    :return: A pandas dataframe containing the data
    """

    # Make a request to the GitHub API
    r = requests.get('https://api.github.com/repos/' + project + '/issues?milestone=' + milestone + '&state=all',
                     auth=(username, pat))

    # Create a new pandas dataframe with only the columns we need
    df = pd.DataFrame(columns=['title', 'state', 'created_at', 'closed_at', 'updated_at'])

    # Iterate through the issues
    for issue in r.json():
        # Add the issue to the dataframe
        df = df.append({'title': issue['title'],
                        'state': issue['state'],
                        'created_at': issue['created_at'],
                        'closed_at': issue['closed_at'],
                        'updated_at': issue['updated_at']}, ignore_index=True)

    # Return the dataframe
    return df


def get_milestone_dates(project, milestone, username, pat):
    """
    Get the milestone start date and end date from the api
    :param project: The GitHub project name
    :param milestone: The GitHub milestone number
    :param username: The GitHub username
    :param pat: The GitHub personal access token
    :return: The milestone start date and end date
    """

    # Make a request to the GitHub API
    r = requests.get('https://api.github.com/repos/' + project + '/milestones/' + milestone,
                     auth=(username, pat))

    # Get the milestone start date and end date
    start_date = r.json()['created_at']
    end_date = r.json()['due_on']

    # Return the milestone start date and end date formatted as YYYY-MM-DD
    return pd.to_datetime(start_date).date(), pd.to_datetime(end_date).date()


def get_commits(project, start_date, end_date, username, pat):
    """
    Pull the data from GitHub
    :param project: The GitHub project name
    :param start_date: The milestone start date
    :param end_date: The milestone end date
    :param username: The GitHub username
    :param pat: The GitHub personal access token
    :return: A pandas dataframe containing the data
    """

    d = pd.DataFrame()

    # There will be multiple pages of commits, so we need to loop through them
    for page in range(1, 100):
        # Make a request to the GitHub API
        r = requests.get('https://api.github.com/repos/' + project + '/commits?page=' + str(page),
                         auth=(username, pat))

        d = pd.concat([d, pd.DataFrame(r.json())])

        # If there are no more commits, break out of the loop
        if len(r.json()) == 0:
            break

    # Filter the commits to only include the columns sha and the commit date which is commit.author.date
    d = d[['sha', 'commit']]
    d['commit'] = d['commit'].apply(lambda x: x['author']['date'])

    # Rename the commit column to be created_at
    d = d.rename(columns={'commit': 'created_at'})

    # Change the data so each date time field is a date with the format YYYY-MM-DD
    d['created_at'] = pd.to_datetime(d['created_at']).dt.date

    # Filter the commits to only include those between the start and end date
    d = d[(d['created_at'] >= start_date) & (d['created_at'] <= end_date)]

    print(d)

    # Return the dataframe
    return d


def generate_burndown_chart(data, commits, start_date, end_date):
    """
    Generate the burndown chart
    :param data: A pandas dataframe containing the data
    :param commits: A pandas dataframe containing the commits
    :param start_date: The milestone start date
    :param end_date: The milestone end date
    """

    # Change the data so each date time field is a date with the format YYYY-MM-DD
    data['created_at'] = pd.to_datetime(data['created_at']).dt.date
    data['updated_at'] = pd.to_datetime(data['updated_at']).dt.date
    data['closed_at'] = pd.to_datetime(data['closed_at']).dt.date

    # Create a list of dates from the earliest created date to the latest closed date
    dates = pd.date_range(start_date, end_date).tolist()

    # Create a new pandas dataframe with the dates as the index
    df = pd.DataFrame(index=dates)

    # Create a new column for the number of issues
    df['total_issues'] = 0

    # Create a new column for the number of issues opened
    df['issues_opened'] = 0

    # Create a new column for the number of issues closed
    df['issues_closed'] = 0

    # Iterate through the dates in the dataframe
    for date in df.index:
        for index, row in data.iterrows():
            # If the issue was created before the date and is still open, increment the number of issues
            if row['created_at'] <= date and row['closed_at'] is NaT:
                df.at[date, 'total_issues'] += 1

            # If the issue was created before the date and is closed after the date, increment the number of issues
            if row['created_at'] <= date < row['closed_at']:
                df.at[date, 'total_issues'] += 1

            # If the issue was created on the date, increment the number of issues opened
            if row['created_at'] == date:
                df.at[date, 'issues_opened'] += 1

            # If the issue was closed on the date, increment the number of issues closed
            if row['closed_at'] == date:
                df.at[date, 'issues_closed'] += 1

    # Set the x-axis to be each date in range of the start date and end date
    index = pd.date_range(start_date, end_date)
    labels = index.strftime('%m-%d')
    plt.xticks(index, labels, rotation=45)
    plt.plot(df.index, df['total_issues'])

    # Create another line on the chart that draws a straight line (start date, total issues) to (end date, 0)
    plt.plot([start_date, end_date], [len(data), 0])

    # Create bars on the chart that show the number of issues opened and closed each day side by side
    sub_plot = plt.subplot()
    sub_plot.bar(df.index - datetime.timedelta(days=0.2), df['issues_opened'], width=0.4, color='g')
    sub_plot.bar(df.index + datetime.timedelta(days=0.2), df['issues_closed'], width=0.4, color='r')

    # Add a line to the graph that shows the commits per day
    commits['created_at'] = pd.to_datetime(commits['created_at']).dt.date
    commits = commits.groupby('created_at').count()
    plt.plot(commits.index, commits['sha'])

    # Create a legend
    plt.legend(['Total Issues', 'Ideal Burndown', 'Commits', 'Issues Opened', 'Issues Closed'])

    plt.show()


if __name__ == '__main__':
    main()
