import { initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'

const firebaseConfig = {
  apiKey: "AIzaSyABrePV_NtzO6sj80q0_wdviacvXTBaUeo",
  authDomain: "lifeskill-53ac9.firebaseapp.com",
  projectId: "lifeskill-53ac9",
  storageBucket: "lifeskill-53ac9.firebasestorage.app",
  messagingSenderId: "850731647181",
  appId: "1:850731647181:web:b9a201451b958639a36984",
  measurementId: "G-PRTVHG9D6T"
};
const app = initializeApp(firebaseConfig)
const auth = getAuth(app)

export { auth }