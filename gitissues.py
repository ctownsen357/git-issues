import json
import requests
import argparse
import csv
import sqlite3


def make_github_issue(username, password, repo_owner, repo_name, title, body=None, assignee=None, milestone=None, labels=None):
    """Creates an issue on github.com using the specified parameters."""
    url = 'https://api.github.com/repos/%s/%s/issues' % (repo_owner, repo_name)
    # Create an authenticated session to create the issue
    session = requests.Session()
    session.auth = (username, password)
    # Create our issue
    issue = {'title': title,
             'body': body,
             'assignee': assignee,
             'milestone': milestone,
             'labels': labels}

    # Add the issue to our repository
    r = session.post(url, json.dumps(issue))
    if r.status_code != 201:
        print 'status_code = {sc}'.format(sc=r.status_code)
        print 'Could not create Issue "%s"' % title
        print 'Response:', r.content


def file_len(fname):
    """returns the number of lines in a file"""
    with open(fname) as fin:
        for i, l in enumerate(fin):
            pass
    return i + 1

#used the following queries to get the TFS items out of the SQL Server database (TFS 2010, YMMV on other versions of TFS)
#            select LT.ID, LT.AddedDate as AddedDate, WL.Title, LT.Words as Words, WL.[Work Item Type], WL.Fld10002 as ItemPriority
#            into ##data
#            from WorkItemLongTexts as LT
#            JOIN WorkItemsAre as WIA ON WIA.ID = LT.ID
#            join WorkItemsLatest as WL ON WL.ID = LT.ID
#            WHERE WIA.State not in ('Done', 'Removed')
#This query was then used to collapse some entries that had duplicate IDs in the system with different "descriptions 'Words' in the TFS 2010 nomenclature."
#I used the SQL Server data export feature and specified that the output CSV had | as the separator.
#            select ID, MAX(AddedDate) as AddedDate, Title, [Work Item Type] as WorkItemType, ItemPriority,
#            CAST(STUFF(( select ' | '  +  cast(Words as varchar(max)) from ##data as d2 where d2.ID = d1.ID FOR XML PATH(''), TYPE).value('.[1]', 'nvarchar(max)'), 1, 2, '') as varchar(max)) as body
#            from ##data as d1
#            group by ID, Title, [Work Item Type], ItemPriority
#            order by ID

#make_github_issue('Issue Title', 'Body text', 'assigned_user', 3, ['bug'])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', help='User name for Git account', required=True)
    parser.add_argument('-p', '--password', help='Password for Git account', required=True)
    parser.add_argument('-o', '--repoowner', help='Repo OWNER for Git account to create issues under', required=True)
    parser.add_argument('-r', '--reponame', help='Git repo to create issues under', required=True)
    parser.add_argument('-c', '--csv', help='CSV file with issues to load into the Git repo', required=True)
    args = parser.parse_args()

    conn = sqlite3.connect('trackdone.db')
    cur = conn.cursor()
    sql = 'create table if not exists track_proc_ids(id integer)'
    cur.execute(sql)

    try:
        #my csv format, based on the query listed above, was: ID, AddedDate, Title, Words, WorkItemType, ItemPriority : TAB delimiter
        with open(args.csv, 'r') as fin:
            reader = csv.reader(fin, delimiter = '\t')
            bad_lines = []
            for line in reader:
                if len(line) != 6:
                    bad_lines.append(line) #in my case TFS introduced all sorts of markup that was included in the file but easilly detected based on the line length
                else: #a good line to process
                    sql = 'select count(*) from track_proc_ids where id = {id}'.format(id=line[0])
                    cur.execute(sql)
                    rslt = cur.fetchone()
                    if rslt[0] == 0:
                        title = line[2]
                        words = line[3]
                        work_item_type = line[4]
                        priority = line[5]

                        mile_stone = 5 #I ended up hovering over the edit milestone link on the github website to see what the integer value was for my milestones
                        label = ['product-backlog']
                        if work_item_type == 'Bug':
                            mile_stone = 2
                            label.append('bug')

                        make_github_issue(args.username, args.password, args.repoowner, args.reponame, title, body=words, assignee=None, milestone=mile_stone, labels=label)
                        sql = 'insert into track_proc_ids(id) values({id})'.format(id=line[0])
                        cur.execute(sql)
                        conn.commit()
    except:
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
