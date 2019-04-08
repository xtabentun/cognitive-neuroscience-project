# Video Annotation Tool
This is a web app for measuring and analysing emotional reactions to videos.

While watching videos, people can indicate their emotional valence. In a seperate view for researchers, the answers people give can be analysed.

This software was written as part of the course _Data Science Project_ at the University of Helsinki in spring 2019.

## Installing required packages

With pip:

```
$ pip install -r requirements.txt
```

or with Anaconda:

```
$ conda install --yes --file requirements.txt
```

## Running the app

To start the app, run: (see below for development/debugging mode)

```
$ export FLASK_APP=video_annotator.py

$ flask run
```
----------------
In development mode, if changes are made to the source code while the app is running, they are automatically and immediately applied to the running app.

If you want to run the app in development mode, run this before starting the app:

```
$ export FLASK_ENV=development
```
(replace ``development`` with ``production`` for production mode)

If you want to switch debugging on, run this before starting the app:
```
$ export FLASK_DEBUG=true
```
(replace ``true`` with ``false`` to switch off debugging)

-----------------
By default the app will connect to and use a database that is hosted online. There is no need to care about this. But if you want another database, set this environment variable:
```
$ export DB_TYPE=dev
```
(you can use ``dev`` for the development database, ``local`` for a local database
  and ``prod`` for the default production database)

The production and development database are hosted online, which means that other people might access them and write data into them as well. The local one will be hosted on your local machine. This option requires MongoDB to be installed and running. [Here](https://docs.mongodb.com/manual/administration/install-community/) are further instructions. MongoDB should be accessible at its default port when running.

## Authors
* [Pihla Toivanen](https://github.com/UMTti)
* [Lea K](https://github.com/xtabentun)
* [Llode](https://github.com/Llode)
* [Moritz Lange](https://github.com/moritzlange)

## License
Published under the MIT license.
