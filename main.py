import firebase_admin
from firebase_admin import credentials
from flask import Flask, request, render_template, flash,Response, stream_with_context
from firebase_admin import firestore
from firebase_admin import messaging
import time
import jsonify
#Verficar si esta instalado Response, stream_with_context


# cedential firebase notification stv
cred = credentials.Certificate("notificationstv-.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# credential correct
credentiaLogin = False

locationUpdate = ""

app = Flask(__name__)

def return_control(nameRequest):
    tokensDb = db.collection('tokens')
    dataToken = list(tokensDb.stream())
    return render_template('control.html', dataToken=dataToken, nameRequest=nameRequest,locationUpdate=locationUpdate)

@app.route('/inicio',methods=['GET'])
def inicio():
    return render_template('login_template.html')

@app.route('/')
def index():
    return render_template('login_template.html')


@app.route('/control', methods=['POST'])
def control():
    # global credential exit
    global credentiaLogin
    if credentiaLogin:
        print("correcto")
        return return_control("Actualizado")


@app.route('/login', methods=['POST'])
def login():
    #global credential exit
    global credentiaLogin

    # get data users
    username = request.form['username']
    password = request.form['password']

    # get if request is equalli data local
    users_ref = db.collection('user')
    query = users_ref.where('name', '==', username).where('pass', '==', password).limit(1)
    listResult = list(query.stream())
    print(listResult)
    credentiaLogin = True

    # number results in listResult
    if len(listResult) > 0:
        return return_control("login")
    else:
        return render_template('login_template.html', mensaje="Error en usuario o contraseña")


# send notification push to phone
# http://videosurnet.co:8080/surnet/ricaurte/5.m3u8
# http://videosurnet.co:8080/surnet/ricaurte/6.m3u8
def send_notipush(token_user, url):
    return True
    #Por ahora no usaremos notification push, con el metodo listener de firestore basta
    '''try:
        message = messaging.Message(
            notification=messaging.Notification(
                title="hola",
                body=url
            ),
            token=token_user)
        response = messaging.send(message)
        print("mensaje enviado correctamente.", response)
        return True
    except Exception as e:
        print("Error con token", e)
        return False'''


@app.route('/update', methods=['POST'])
def update():
    global locationUpdate    
    if len(request.form['token']) > 0:
        locationUpdate = request.form['location']
        action = request.form['action']
        print(action)
        # if action origin button update
        if action == 'Actualizar':
            db_ref = db.collection("tokens")
            # filtra los documentos por el campo 'location'
            query = db_ref.where('token', '==', request.form['token'])
            # obtiene un querysnapshot de los elementos que cumplen el filtro
            result = query.get()

            if len(result) > 0:
                sendPush = False
                for data in result:
                    # obtiene la referencia del documento
                    doc_ref = data.reference
                    print("referencia", doc_ref)
                    # actualizamos los campos de la base de datos
                    doc_ref.update({'token': request.form['token'], 'nombre':request.form['nombre'],'location': request.form['location'],
                                    'url_current': request.form['url']})
                    # send message exit
                    sendPush = send_notipush(request.form['token'], request.form['url'])

                # this case no equally
                if sendPush:
                    return return_control("Actualizacion Correcta")
                else:
                    return return_control("Error con token, Se actualizo bd, pero no se envio Notification Push")
            elif action == 'Eliminar':
                print("No existen coincidencias")
        if action == 'Adicionar':
            locationUpdate = ""
            print("adicionar")
            print(request.form['location'])
            doc_ref = db.collection("tokens").document()
            doc_ref.set({
                'token': request.form['token'],
                'location': request.form['location'],
                'url_current': request.form['url'],
                'nombre':request['nombre']
            })
            return return_control("Adicion Correcta")

        if action == 'Eliminar':
            locationUpdate = ""
            # Crear una referencia a la colección "tokens"
            doc_ref = db.collection("tokens")
            # Crear una consulta que filtre los documentos por la ubicación que se recibe del formulario
            query = doc_ref.where('location', '==', request.form['location']).where('token', '==',
                                                                                    request.form['token'])
            # Obtener los documentos que cumplen con la consulta y contar cuántos son
            num_results = len(query.get())

            docs = query.get()

            if num_results > 0:
                for res in docs:
                    doc_ref = res.reference
                    # delete content
                    doc_ref.delete()
                return return_control("Eliminado correctamente")
            else:
                return return_control("No encontro resultados")

    else:
        return return_control("")


#Solicitamos las ciudades vinculadas
@app.route('/api/data', methods=['GET'])
def get_data():
    tokensDb = db.collection('ciudades') 
    dataToken = list(tokensDb.stream())

    # Crear una lista para almacenar los datos
    ciudades = []

    # Recorrer los documentos y obtener sus datos
    for doc in dataToken:
        ciudad_data = doc.to_dict()  # Convierte el documento a un diccionario
        ciudad_data['name_ciud'] = doc.id    # Añadir el ID del documento
        ciudades.append(ciudad_data)

    # Retornar una respuesta en formato JSON
    return jsonify({
        'status': 'success',
        'request': "",
        'ciudades': ciudades
    })


if __name__ == "__main__":
     app.run(host='0.0.0.0',port=4001) 
    #app.run(debug=True)
    # app.run(host='0.0.0.0', port=4001)