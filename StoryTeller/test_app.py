import unittest
import json
from flask import Flask
from app import app



class CustomTestResult(unittest.TestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        print(f'{test}: ("exito")')

    def addFailure(self, test, err):
        super().addFailure(test, err)
        print(f'{test}: ("fracaso")')

    def addError(self, test, err):
        super().addError(test, err)
        print(f'{test}: ("error")')


class CustomTextTestRunner(unittest.TextTestRunner):
    resultclass = CustomTestResult




class AppTestCase(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()

#REGISTRO 
    #200
    '''def test_register_user(self):
        # datos de prueba para el registro de usuario
        user_data = {
            "email": "test5@example.com",
            "username": "testuser",
            "password": "testpassword",
        }

        # realizar una solicitud POST a la ruta '/user' con los datos del usuario
        response = self.client.post("/user", json=user_data)
        data = json.loads(response.data)

        #print("\tRegister_user_data: ", data)

        # verificar si la respuesta es exitosa y contiene la clave 'ok' con valor True
        self.assertTrue(data["ok"])
        # verificar si la respuesta contiene las claves 'email', 'name', 'profile_picture' y 'token'
        self.assertIn("email", data)
        self.assertIn("name", data)
        self.assertIn("profile_picture", data)
        self.assertIn("token", data)
        self.assertNotIn(b'No hay entradas', data)'''
        
    
    #400
    def test_register_user_missing_password(self):
        # datos de prueba con campos faltantes para el registro de usuario
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            # Faltando el campo 'password'
        }

        # realizar una solicitud POST a la ruta '/user' con los datos del usuario
        response = self.client.post("/user", json=user_data)
        data = json.loads(response.data)

        # verificar si la respuesta tiene un codigo de estado 400 (solicitud incorrecta)
        self.assertEqual(response.status_code, 400)
        # verificar si la respuesta contiene la clave 'ok' con valor False
        self.assertFalse(data["ok"])
        # verificar si la respuesta contiene la clave 'msg' con un mensaje de error
        self.assertIn("msg", data)


    def test_register_user_missing_email(self):
        # datos de prueba con campos faltantes para el registro de usuario
        user_data = {
            # Faltando el campo 'email'
            "username": "testuser",
            "password": "testpassword",
        }

        # realizar una solicitud POST a la ruta '/user' con los datos del usuario
        response = self.client.post("/user", json=user_data)
        data = json.loads(response.data)

        # verificar si la respuesta tiene un codigo de estado 400 (solicitud incorrecta)
        self.assertEqual(response.status_code, 400)
        # verificar si la respuesta contiene la clave 'ok' con valor False
        self.assertFalse(data["ok"])
        # verificar si la respuesta contiene la clave 'msg' con un mensaje de error
        self.assertIn("msg", data)
    

    def test_register_user_missing_username(self):
        # datos de prueba con campos faltantes para el registro de usuario
        user_data = {
            "email": "test@example.com",
            # Faltando el campo 'username'
            "password": "testpassword",
        }

        # realizar una solicitud POST a la ruta '/user' con los datos del usuario
        response = self.client.post("/user", json=user_data)
        data = json.loads(response.data)

        # verificar si la respuesta tiene un codigo de estado 400 (solicitud incorrecta)
        self.assertEqual(response.status_code, 400)
        # verificar si la respuesta contiene la clave 'ok' con valor False
        self.assertFalse(data["ok"])
        # verificar si la respuesta contiene la clave 'msg' con un mensaje de error
        self.assertIn("msg", data)
    

    def test_register_user_missing_all(self):
        # datos de prueba con campos faltantes para el registro de usuario
        user_data = {
            # Faltando el campo 'email'
            # Faltando el campo 'username'
            # Faltando el campo 'password'
        }

        # realizar una solicitud POST a la ruta '/user' con los datos del usuario
        response = self.client.post("/user", json=user_data)
        data = json.loads(response.data)

        # verificar si la respuesta tiene un codigo de estado 400 (solicitud incorrecta)
        self.assertEqual(response.status_code, 400)
        # verificar si la respuesta contiene la clave 'ok' con valor False
        self.assertFalse(data["ok"])
        # verificar si la respuesta contiene la clave 'msg' con un mensaje de error
        self.assertIn("msg", data)
    
    
    #409
    def test_register_user_already_registered(self):
        # datos de prueba con campos faltantes para el registro de usuario
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword",
        }

        response = self.client.post("/user", json=user_data)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 409)
        # verificar si la respuesta contiene la clave 'ok' con valor False
        self.assertFalse(data["ok"])
        # verificar si la respuesta contiene la clave 'msg' con un mensaje de error
        self.assertIn("msg", data)

#LOGGIN
    #200
    def test_login_user(self):
        # datos de prueba para iniciar sesión
        user_data = {
            "type": "regular",
            "email": "test@example.com",
            "password": "testpassword",
        }

        # realizar una solicitud POST a la ruta '/user/login' con los datos de inicio de sesion
        response = self.client.post("/user/login", json=user_data)
        data = json.loads(response.data)

        self.assertTrue(data["ok"])
        # verificar si la respuesta contiene las claves 'email', 'name', 'profile_picture' y 'token'
        self.assertIn("email", data)
        self.assertIn("name", data)
        self.assertIn("profile_picture", data)
        self.assertIn("token", data)

        # verificar si la respuesta tiene un codigo de estado 200 (OK)
        self.assertEqual(response.status_code, 200)


    def test_login_user_missing_email(self):
        # datos de prueba para iniciar sesión
        user_data = {
            "type": "regular",
            # Faltando el campo 'email'
            "password": "testpassword",
        }

        # realizar una solicitud POST a la ruta '/user/login' con los datos de inicio de sesion
        response = self.client.post("/user/login", json=user_data)
        data = json.loads(response.data)

        # verificar si la respuesta tiene un codigo de estado 400 (solicitud incorrecta)
        self.assertEqual(response.status_code, 400)
        # verificar si la respuesta contiene la clave 'ok' con valor False
        self.assertFalse(data["ok"])
        # verificar si la respuesta contiene la clave 'msg' con un mensaje de error
        self.assertIn("msg", data)

    
    def test_login_user_missing_password(self):
        # datos de prueba para iniciar sesión
        user_data = {
            "type": "regular",
            "email": "test@example.com",
            # Faltando el campo 'password'
        }

        # realizar una solicitud POST a la ruta '/user/login' con los datos de inicio de sesion
        response = self.client.post("/user/login", json=user_data)
        data = json.loads(response.data)

        # verificar si la respuesta tiene un codigo de estado 400 (solicitud incorrecta)
        self.assertEqual(response.status_code, 400)
        # verificar si la respuesta contiene la clave 'ok' con valor False
        self.assertFalse(data["ok"])
        # verificar si la respuesta contiene la clave 'msg' con un mensaje de error
        self.assertIn("msg", data)
    

    def test_login_user_missing_all(self):
        # datos de prueba para iniciar sesión
        user_data = {
            # Faltando el campo 'email'
            # Faltando el campo 'password'
        }

        # realizar una solicitud POST a la ruta '/user/login' con los datos de inicio de sesion
        response = self.client.post("/user/login", json=user_data)
        data = json.loads(response.data)

        # verificar si la respuesta tiene un codigo de estado 400 (solicitud incorrecta)
        self.assertEqual(response.status_code, 400)
        # verificar si la respuesta contiene la clave 'ok' con valor False
        self.assertFalse(data["ok"])
        # verificar si la respuesta contiene la clave 'msg' con un mensaje de error
        self.assertIn("msg", data)

#STORY

    def test_story_prompts(self):
        # iniciamos sesion con el usuario de prueba y obtenemos el token
        user = {
            "type": "regular",
            "email": "test@example.com",
            "password": "testpassword"
        }
        login_response = self.client.post('/user/login', data=json.dumps(user), content_type='application/json')
        login_data = json.loads(login_response.get_data(as_text=True))
        token = login_data['token']

        # esta es una historia de prueba que usaremos para la solicitud.
        story = {
            "story": "this is a test..."
        }

        # realizamos una peticion POST a la ruta /story/prompts con la historia de prueba
        # incluimos el token en la cabecera 'Authorization'
        response = self.client.post('/story/prompts', 
                                data=json.dumps(story), 
                                content_type='application/json',
                                headers={'Authorization': 'Bearer ' + token})
        data = json.loads(response.get_data(as_text=True))

        #print("\tStory_promps_data: ", data)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(data['ok'], True)

        # Verificamos que la respuesta contenga un campo 'queries' que es una lista (puede estar vacia si no se generaron consultas).
        self.assertIsInstance(data['queries'], list)

    
    def test_story_prompts_missingStory(self):
        # iniciamos sesion con el usuario de prueba y obtenemos el token
        user = {
            "type": "regular",
            "email": "test@example.com",
            "password": "testpassword"
        }
        login_response = self.client.post('/user/login', data=json.dumps(user), content_type='application/json')
        login_data = json.loads(login_response.get_data(as_text=True))
        token = login_data['token']

        # esta es una historia de prueba que usaremos para la solicitud.
        story = {}

        # realizamos una peticion POST a la ruta /story/prompts con la historia de prueba
        # incluimos el token en la cabecera 'Authorization'
        response = self.client.post('/story/prompts', 
                                data=json.dumps(story), 
                                content_type='application/json',
                                headers={'Authorization': 'Bearer ' + token})
        data = json.loads(response.get_data(as_text=True))

        # verificar si la respuesta tiene un codigo de estado 400 (solicitud incorrecta)
        self.assertEqual(response.status_code, 400)
        # verificar si la respuesta contiene la clave 'ok' con valor False
        self.assertFalse(data["ok"])
        # verificar si la respuesta contiene la clave 'msg' con un mensaje de error
        self.assertIn("msg", data)


    def test_story_get(self):
        # iniciamos sesion con el usuario de prueba y obtenemos el token
        user = {
            "type": "regular",
            "email": "test@example.com",
            "password": "testpassword"
        }
        login_response = self.client.post('/user/login', data=json.dumps(user), content_type='application/json')
        login_data = json.loads(login_response.get_data(as_text=True))
        token = login_data['token']

        title = {
            "title": "Test title"
        }

        response = self.client.get('/story', 
                                data=json.dumps(title), 
                                content_type='application/json',
                                headers={'Authorization': 'Bearer ' + token})
        data = json.loads(response.get_data(as_text=True))
        #print("\tStory_get_data: ", data)

        self.assertEqual(response.status_code, 200)


    
    def test_story_post(self):
        # iniciamos sesion con el usuario de prueba y obtenemos el token
        user = {
            "type": "regular",
            "email": "test@example.com",
            "password": "testpassword"
        }
        login_response = self.client.post('/user/login', data=json.dumps(user), content_type='application/json')
        login_data = json.loads(login_response.get_data(as_text=True))
        token = login_data['token']
        
        title = {
            "title": "Test title"
        }

        response = self.client.post('/story', 
                                data=json.dumps(title), 
                                content_type='application/json',
                                headers={'Authorization': 'Bearer ' + token})
        data = json.loads(response.get_data(as_text=True))
        #print("\tStory_post_data: ", data)
         # verificamos que la respuesta tenga un codigo de estado 200, lo que indica que la solicitud fue exitosa
        self.assertEqual(response.status_code, 200)

        # verificamos que el campo 'ok' en la respuesta sea True, lo que indica que la solicitud fue procesada correctamente
        self.assertEqual(data['ok'], True)
        #self.assertIsInstance(data['story_id'], int)
    

    def test_create_images(self):
        # iniciamos sesion con el usuario de prueba y obtenemos el token
        user = {
            "type": "regular",
            "email": "test@example.com",
            "password": "testpassword"
        }
        login_response = self.client.post('/user/login', data=json.dumps(user), content_type='application/json')
        login_data = json.loads(login_response.get_data(as_text=True))
        token = login_data['token']

        # datos de prueba para generar imagenes reales y almacenar en la base de datos
        images_data = {
            "query": "test query",
            "story_id": 5,
            "for_real": True,
            "n_images": 1,
        }

        # realizar una solicitud POST a la ruta '/image/create' con los datos de generacion de imagenes y el token de acceso
        response = self.client.post(
            "/image/create",
            json=images_data,
            headers={'Authorization': 'Bearer ' + token},
        )
        data = json.loads(response.data)
        #print("\tImages_data: ", data)

        # verificar si la respuesta es exitosa y contiene la clave 'ok' con valor True
        self.assertTrue(data["ok"])

        self.assertIn("images", data)
        self.assertIsInstance(data["images"], list)
        self.assertEqual(len(data["images"]), images_data["n_images"])

        # verificar si la respuesta tiene un codigo de estado 200 (OK)
        self.assertEqual(response.status_code, 200)


    def test_image_hash(self):
        # iniciamos sesion con el usuario de prueba y obtenemos el token
        user = {
            "type": "regular",
            "email": "test@example.com",
            "password": "testpassword"
        }
        login_response = self.client.post('/user/login', data=json.dumps(user), content_type='application/json')
        login_data = json.loads(login_response.get_data(as_text=True))
        token = login_data['token']

        response = self.client.get(
            "/image/f030fdbac5a2b1d09e865853eafa12ce45bd3db25fb387ac04dc66e325d5d514",
            headers={'Authorization': 'Bearer ' + token},
        )
        
        self.assertEqual(response.status_code, 200)
    

    def test_image(self):
        # iniciamos sesion con el usuario de prueba y obtenemos el token
        user = {
            "type": "regular",
            "email": "test@example.com",
            "password": "testpassword"
        }
        login_response = self.client.post('/user/login', data=json.dumps(user), content_type='application/json')
        login_data = json.loads(login_response.get_data(as_text=True))
        token = login_data['token']


        response = self.client.get('/image', 
                                headers={'Authorization': 'Bearer ' + token})
        data = json.loads(response.get_data(as_text=True))
        #print(data)

        self.assertEqual(response.status_code, 200)
    

    def test_style_get(self):
        # iniciamos sesion con el usuario de prueba y obtenemos el token
        user = {
            "type": "regular",
            "email": "test@example.com",
            "password": "testpassword"
        }
        login_response = self.client.post('/user/login', data=json.dumps(user), content_type='application/json')
        login_data = json.loads(login_response.get_data(as_text=True))
        token = login_data['token']

        response = self.client.get('/style', 
                                headers={'Authorization': 'Bearer ' + token})
        data = json.loads(response.get_data(as_text=True))
        #print("\tStyles_data: ", data)

        self.assertEqual(response.status_code, 200)
        

    '''def test_style_post(self):
        # iniciamos sesion con el usuario de prueba y obtenemos el token
        user = {
            "type": "regular",
            "email": "test@example.com",
            "password": "testpassword"
        }
        login_response = self.client.post('/user/login', data=json.dumps(user), content_type='application/json')
        login_data = json.loads(login_response.get_data(as_text=True))
        token = login_data['token']
        
        style = {
            "style": "cartoon"
        }

        response = self.client.post('/style', 
                                data=json.dumps(style), 
                                content_type='application/json',
                                headers={'Authorization': 'Bearer ' + token})
        data = json.loads(response.get_data(as_text=True))
        print(data)
        
        self.assertEqual(response.status_code, 200)

        self.assertEqual(data['ok'], True)'''
        


if __name__ == "__main__":
    unittest.main(testRunner=CustomTextTestRunner())
