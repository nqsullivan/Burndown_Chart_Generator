import datetime

import requests
import pandas as pd
import matplotlib.pyplot as plt
from pandas import NaT


def main():
    """
    A script to generate a burndown chart from a github milestone
    """

    # Prompt the user for the github project
    # project = input('Enter the github project (e.g. nqsullivan/Burndown_Chart_Generator): ')
    project = 'amehlhase316/Kopfkino-Spring23C'

    # Prompt the user for the github milestone
    milestone = input('Enter the github milestone (e.g. 1): ')

    # Prompt the user for the github username
    username = input('Enter the github username: ')

    # Prompt the user for the github personal access token
    pat = input('Enter the github personal access token: ')

    # Pull the data from github
    data = get_data(project, milestone, username, pat)

    # Get the milestone start date and end date from the api
    start_date, end_date = get_milestone_dates(project, milestone, username, pat)

    # Generate the burndown chart
    generate_burndown_chart(data, start_date, end_date)


def get_data(project, milestone, username, pat):
    """
    Pull the data from github
    :param project: The github project name
    :param milestone: The github milestone number
    :param username: The github username
    :param pat: The github personal access token
    :return: A pandas dataframe containing the data
    """

    # Make a request to the github API
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
    :param project: The github project name
    :param milestone: The github milestone number
    :param username: The github username
    :param pat: The github personal access token
    :return: The milestone start date and end date
    """

    # Make a request to the github API
    r = requests.get('https://api.github.com/repos/' + project + '/milestones/' + milestone,
                     auth=(username, pat))

    # Get the milestone start date and end date
    start_date = r.json()['created_at']
    end_date = r.json()['due_on']

    # Return the milestone start date and end date formatted as YYYY-MM-DD
    return pd.to_datetime(start_date).date(), pd.to_datetime(end_date).date()


def generate_burndown_chart(data, start_date, end_date):
    """
    Generate the burndown chart
    :param data: A pandas dataframe containing the data
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

    # Set the x axis to be each date in range of the start date and end date
    index = pd.date_range(start_date, end_date)
    labels = index.strftime('%m-%d')
    plt.xticks(index, labels, rotation=45)
    plt.plot(df.index, df['total_issues'])

    # Create another line on the chart that draws a straight line (startdate, total issues) to (enddate, 0)
    plt.plot([start_date, end_date], [len(data), 0])

    # Create bars on the chart that show the number of issues opened and closed each day side by side
    sub_plot = plt.subplot()
    sub_plot.bar(df.index - datetime.timedelta(days=0.2), df['issues_opened'], width=0.4, color='g')
    sub_plot.bar(df.index + datetime.timedelta(days=0.2), df['issues_closed'], width=0.4, color='r')

    plt.show()


if __name__ == '__main__':
    main()
