# git-issues
Python script to import issues from TFS 2010 via CSV file to Git repo

### Usage:
First export your TFS items to a CSV file, I'd recommend using the built in SQL Server extract data function and using TAB as your delimiter - it will most likely take
some experimenting to get it to work correctly.  The following two queries are what I used:

```sql
-- notice I select it into a global table so that it may be referenced by the export utility later
select LT.ID, LT.AddedDate as AddedDate, WL.Title, LT.Words as Words, WL.[Work Item Type], WL.Fld10002 as ItemPriority
into ##data
from WorkItemLongTexts as LT
JOIN WorkItemsAre as WIA ON WIA.ID = LT.ID
join WorkItemsLatest as WL ON WL.ID = LT.ID
WHERE WIA.State not in ('Done', 'Removed')
```

This is the query I ran in the export utility.  I did this with STUFF as there was a bug in TFS 2010 that was causing duplicate entries into the database or
entries that were entered via the TFS utility would store data in one record and the web interface another.  This query ensures that for any given ID I have all of the
text data concatenated together:
```sql
select ID, MAX(AddedDate) as AddedDate, Title, [Work Item Type] as WorkItemType, ItemPriority,
CAST(STUFF(( select ' | '  +  cast(Words as varchar(max)) from ##data as d2 where d2.ID = d1.ID FOR XML PATH(''), TYPE).value('.[1]', 'nvarchar(max)'), 1, 2, '') as varchar(max)) as body
from ##data as d1
group by ID, Title, [Work Item Type], ItemPriority
order by ID
```

Save the CSV somewhere and then it is just a matter of running the script:
```shell
python gitissues.py -u you@youraccount.com -p your_password_or_auth_token -o repo-owner -r repo -c your.csv
```
gitussues.py uses the args package so you may run it without any arguments and the script will report what is required and what the switch options are.
