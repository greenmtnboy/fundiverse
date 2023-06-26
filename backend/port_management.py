

def get_service_name(port):
    import psutil

    for conn in psutil.net_connections():
        if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port:
            pid = conn.pid
            try:
                service_name = psutil.Process(pid).name()
                return service_name
            except psutil.Error:
                return "Unknown"
    return "Not in use"


if __name__ == "__main__":

    # Specify the port you want to check
    port = 3000

    # Get the service name associated with the port
    service_name = get_service_name(port)

    print(f"The service running on port {port} is: {service_name}")