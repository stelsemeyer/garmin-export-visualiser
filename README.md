## Garmin export visualiser widget

### Why

Unfortunately Garmin does not allow to visualise multiple years of data. For this reason I created very simple widget (find the link [below](#Website)) 
to visualise metrics like resting heart rate or activity duration over time:

![newplot](https://github.com/stelsemeyer/garmin-export-visualiser/assets/18263836/2cd4ba69-ece1-4ca7-b95d-07a289995816)

### Garmin data export

On the [Garmin website](garmin.com) you can request a data export via the following way:

```
-> User icon (in the top right)
-> Account
-> Data Management
-> Manage Your Data
-> Export Your Data
-> Request Data Export
```

Garmin will then send you a zip file with a lot of data. 

The files `DI_CONNECT/DI-Connect-Aggregator/USDFile_*.json` contain daily aggregates of metrics like resting heart rate, activity meters, etc. 
and can then be uploaded and visualised via the widget. 

### Website

The widget is hosted [here](https://garmin-export-visualiser-dkbkfpugja-ey.a.run.app).

It is deployed continously from the main branch of this repository via Google Cloud Build & Cloud Run.

### Locally

You can run the dash widget locally via python.

1. Install requirements via `pip install -r requirements.txt`.
1. Then run the widget via `python app.py`

### Data

The data you upload is not stored.

### Issues & improvements

If you have any issues, suggestions or want to talk about the widget, please create an issue, open a pull request or write an email to telsemeyerblog@gmail.com.

Thanks!
