# SportsCalendar

This project was made by Konrad Paszynski for the 2nd stage of a job application for sportsradar. It is a prototype of a website for scheduling and viewing sport events. 

The project was made using python 3.11.5. It was made in VScode using the SQLite extension by alexcvzz.  

Before using, make sure the correct packages are installed. Run this line in the command prompt:
pip install -r requirements.txt

After downloading the code:
-If the database isn't populated, right click on sports.db and click 'open database'. Then go to schema.sql, select all, right click and press run selected query. Then do the same inside insert.sql. 
-To open the website, open cmd and navigate to the folder where the code is saved. Then type the following line: python backend\server.py 
If everything is successfull, you should get a 'starting backend' message. Then, insert http://127.0.0.1:5000/ into your browser. 

To run tests, type the following lines in the command prompt:
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pytest -q