from prefect import flow, task


@flow
def helloworld():
    print("Hello, world!")


helloworld()
