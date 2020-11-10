import flaskr

application = flaskr.create_app()

if __name__ == '__main__':
    application.debug = False
    application.run()
