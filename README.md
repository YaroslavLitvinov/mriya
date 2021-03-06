[![Build Status](https://travis-ci.org/YaroslavLitvinov/mriya.svg?branch=master)](https://travis-ci.org/YaroslavLitvinov/mriya)
[![Coverage Status](https://coveralls.io/repos/github/YaroslavLitvinov/mriya/badge.svg?branch=master)](https://coveralls.io/github/YaroslavLitvinov/mriya?branch=master)

# mriya
![Github repo](https://github.com/YaroslavLitvinov/mriya)
The Mriya DMT is a SQL scripting tool created for Salesforce data
transformations. It implements Salesforce Bulk API operations: query,
insert, delete and update that altogeter can be treated as an external
interface of application. Later SOAP merge operation was added to the
list of supported Salesforce operations.  In addition application has
adopted Sqlite3 as a local SQL engine.  So you can create various
transformation scripts just having sequences of SQL commands inside
and using a lot of intermediate staging tables. It's yet another
solution for doing same things which Dataloader and Workbench do.
Sql scripts you created can be visualised by representing all sql
operations as single direct acyclic graph (DAG), it's suitable for
complicated scripts.

A graph example. Click to open it in chrome/firefox.
![example of graph](https://rawgit.com/YaroslavLitvinov/mriya/master/readme/graph.svg)

* Install.<br>Requirements and export PYTHONPATH:
```
apt-get install xdot
pip install -r requirements.txt
export PYTHONPATH=pybulk/sfbulk/:.
py.test --cov-report=term-missing --cov=mriya tests/
```
* Config file.<br>
Use sample-config.ini as a base for your config files.<br>
Specify `[dst]` and `[src]` sections for dst/src endpoints.
```
# Setup an endpoint/s 
[dst]
consumer_key = 
consumer_secret = 
username = 
password = 
host_prefix = 
production = True/False
```
* Major command line params
* Provide config file as well as corresponding endpoints:<br>
```--conf-file config.ini --src-name 'OLD ENDPOINT' --dst-name 'NEW ENDPOINT'```
* Specify one or several jobs:<br>
```--job path/to/some_file1.sql --job path/to/some_file2.sql
```
* You can also provide a job as stdin data, for example:<br>
```echo "
SELECT 'a' as hero => csv:test
SELECT * FROM csv.test => var:TEST_VAR:publish" | python mriya_dmt.py --job-file /dev/stdin ...```

* Define data path as cmd line param, providing of absolute paths could be a good practice:<br>
```--datadir some/data/path```

* Tests<br>
It uses mocks for any http requests made by application tests.

* Troubleshooting<br>
```AttributeError: ConfigParser instance has no attribute 'read_file'```<br>
If you getting that error, be sure to install and use configparser==3.5.0.

* Syntax
Use sqlite3 sql syntax while querying local csv tables, and SF bulk query language when running SF bulk queries. `csv` endpoint means local sqlite3 table and `src` / `dst` endpoints mean remote SF table. When issuing request endpoint's str will be removed from query.<br>
`SELECT 1 from csv.table;` transformates into local sqlite3 query: `SELECT 1 from table;`<br>
`SELECT Id from src.table;` transformates into SF query: `SELECT Id from table;`

* Variables via cmdline.<br>
Add variable/s from cmd line:<br>
```mriya_dmt.py --var MY_USER_ID 00561000001znSnAAI --var ID2 12345```

* Syntax in examples.<br>

Comment is started as `--` at the beginning of line
```sql
-- comment section. 
```

assign value to variable
```sql
SELECT 'field1,field2' => var:FIELDS
```

variable can only be used in query section, and can't be used after `=>`
```sql
SELECT {FIELDS} FROM csv.table => csv:test
```

Publish info at stdout. assign value to variable and put it to stdout
```sql
SELECT 'field1,field2' => var:FIELDS:publish
```

Prevent removing endpoints from value during substitution. Use `=> const:` to mark variable as non changeable during substitution. if `const:` is ommited then endpoint will be always removed. It's useful to use `const:` when using variable during query construction:
```sql
SELECT " 'str' as field1, CAST(field2 as INTEGER) FROM csv.table" \
=> var:FIELDS \
=> const:
SELECT {FIELDS} => csv:newtable
```

Issue bulk request to SF endpoint denoted as `src` and query table `SalesforceTable`, then save result into `csv` file `Opportunity1`<br>
':cache' means use already existing csv file Opportunity1, instead of requesting it again
```sql
SELECT something from src.SalesforceTable => csv:Opportunity1:cache
```

Construct query using variable's value and issue request it to SF instance at `dst`, save result into `csv` file `Opportunity2`
```sql
SELECT Id,{fields} from dst.SalesforceTable => csv:Opportunity2
```

Use `\` to make long single queries fancier by writing them in mulitiple lines. If '\' symbol is located at the end of a row it's will be concatenated with next row. **Any** single query is oneliner.
Following example explanation:<br>
Select data from local `csv` table `Opportunity2` and save it to another `csv` table `Opportunity_something_update` and then submit update bulk request using data from `Opportunity_something_update` table to `dst` SF instance. Save processed list of ids returned by SF into csv table `Update_Result_Ids`. All the content of table will be submitted as list of batches with max batch size = 10000. Batches will be executed one by one as `type:sequential` was specified. Batches would run in parallel if type `type:parallel` or nothing specified [type:parallel is by default]
```sql
SELECT Id, {fields} FROM csv.Opportunity2 \
=> csv:Opportunity_something_update \
=> dst:update:Opportunity:10000:Update_Result_Ids \
=> type:sequential
```

insert, update, delete SF batches are supported.<br>
Examples:
```sql
SELECT f1,f2 FROM csv.foo => csv:export => dst:insert:10000:list_of_processed_ids_errors
SELECT f1,f2 FROM csv.foo => csv:export => dst:delete:10000:list_of_processed_ids_errors
SELECT f1,f2 FROM csv.foo => csv:export => src:update:10000:list_of_processed_ids_errors
```

Macroses<br>
Any sql script considered to be macro if starting as 'macro_' and located in the same directory as job-file<br>
One macro can be nested into another macro<br>
macro will be substituted by its value read from corresponding file.<br>
Macro file `macro_test` is supposed to be existed in scripts folder. All previously defined variables can be used inside of macros. Macro param value should not contains spaces. Many macro params may be specified(params set is different for diferent macroses).
```sql
SELECT 'hello' => var:VAR1 \
=> macro:macro_test \
   :PARAM1:param_value_no_spaces \
   :PARAM2:some_table
```

example of macro file:
```sql
-- {PARAM1}, {PARAM2} will be substituted by param value param_value_no_spaces
-- {VAR1} will be substituted by var value
SELECT {PARAM1}, '{VAR1}' as hello, ID FROM csv.table => csv:{PARAM2}_some_string
-- resulted macro will be transformated into:
SELECT param_value_no_spaces, 'hello' as hello, ID FROM csv.table => csv:some_table_some_string
```

Use following construction to run some code in loop
```sql
-- SELECT_BATCH_IDX - variable having different value on different iterations
-- Query located before '=> batch_begin' is getting a list of values for loop
SELECT CAST(i as INTEGER) as idx FROM csv.ints10000 LIMIT 10 \
=> batch_begin:idx:SELECT_BATCH_IDX
   -- run following code 10 times
   SELECT '{SELECT_BATCH_IDX}' => var:info:publish
=> batch_end:SELECT_BATCH_IDX
```

Soap merge expects csv file with MasterRecordId, MergeRecordId columns, example of using:
```sql
-- Using data in test.csv merge dup records. Batch size value(200) is ignored
SELECT MasterRecordId, MergeRecordId FROM csv.test \
=> csv:Merge_dst_Account \
=> dst:merge:Account:200:Merge_dst_Account_res_ids
```

example of resulted Merge_dst_Account_res_ids.csv:
```csv
Id,Success,StatusCode,Message
"0016100000M94ppAAB","false","ENTITY_IS_DELETED","entity is deleted"
"0016100000M94ppAAA","true","",""
```

Assertion of variable's value. Assert val=0 and val!=0 correspondingly:
```sql
--Assert VAR1=0, will raise exception if VAR1 is not 0
SELECT count() FROM csv.test => var:VAR1:publish => assert:zero

--Assert VAR2!=0, will raise exception if VAR2 is 0
SELECT count() FROM csv.test => var:VAR2:publish => assert:nonzero
```

Limited support of variables added for using outside of queries, after '=>' specified.
Variable can be used with 'csv' key only, like '=> csv:csv_{VARIABLE}_csv', for this case
variable name will be substituted by it's value.
For any other keys variable shouldn't be used outside of query and will be ignored.
```sql
SELECT 'May the force be with you' => var:VARIABLE
SELECT '1' as fieldname => csv:csv_{VARIABLE}_csv
-- it's will be translated into
-- SELECT '1' as fieldname => csv:csv_May the force be with you_csv

SELECT 'var1' => var:VAR1
SELECT '' => var:{VAR1}
-- you will get 2 vars: VAR1=var1, {VAR1}=''
```
