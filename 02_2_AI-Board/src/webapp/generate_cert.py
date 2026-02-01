"""
Self-signed SSL Certificate Generator for AI-Board
---------------------------------------------------
This script generates a self-signed SSL certificate for local HTTPS testing.
Run this script once to create cert.pem and key.pem files.
"""

from OpenSSL import crypto
import os

def generate_self_signed_cert(cert_file="cert.pem", key_file="key.pem"):
    """Generate a self-signed SSL certificate"""
    
    # Create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)
    
    # Create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = "JP"
    cert.get_subject().ST = "Tokyo"
    cert.get_subject().L = "Tokyo"
    cert.get_subject().O = "AI-Board"
    cert.get_subject().OU = "Development"
    cert.get_subject().CN = "localhost"
    
    # Get local IP address
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"
    
    # Add Subject Alternative Names for localhost and IP addresses
    san_list = f"DNS:localhost,DNS:127.0.0.1,IP:127.0.0.1,IP:{local_ip}".encode()
    cert.add_extensions([
        crypto.X509Extension(b"subjectAltName", False, san_list)
    ])
    
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for 1 year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')
    
    # Save certificate
    with open(cert_file, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    
    # Save private key
    with open(key_file, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
    
    print(f"✅ SSL certificate generated successfully!")
    print(f"   - Certificate: {cert_file}")
    print(f"   - Private Key: {key_file}")
    print(f"\n⚠️  This is a self-signed certificate for development only.")
    print(f"   Browsers will show a security warning. Click 'Advanced' and 'Proceed'.")

if __name__ == "__main__":
    # Generate in the same directory as app.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cert_path = os.path.join(script_dir, "cert.pem")
    key_path = os.path.join(script_dir, "key.pem")
    
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print("⚠️  Certificate files already exist.")
        response = input("Do you want to regenerate them? (y/N): ")
        if response.lower() != 'y':
            print("Skipping certificate generation.")
            exit(0)
    
    generate_self_signed_cert(cert_path, key_path)
