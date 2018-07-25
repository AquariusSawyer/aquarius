import pika
import time
import json


class Task:

    def __init__(self):
        self.method = None

    def add(a, b , c):
        print(time.time())
        time.sleep(3)
        return a + b + c

    def implements(self, method):
        self.method = method
        return self

    def __call__(self, *args, **kwargs):

        return self.__class__.__dict__[self.method](*args, **kwargs)


task = Task()

def on_request(ch, method, props, body):


    body = json.loads(body.decode("utf-8"))

    func = body['func']
    args = body['args']
    kwargs = body['kwargs']

    result = task.implements(func)(*args, **kwargs)

    body['result'] = result


    ch.basic_publish(
            exchange='',  # 把执行结果发回给客户端
            routing_key=props.reply_to,  # 客户端要求返回想用的queue
            # 返回客户端发过来的correction_id 为了让客户端验证消息一致性
            properties=pika.BasicProperties(correlation_id = props.correlation_id),
            body=str(body)
    )

    ch.basic_ack(delivery_tag = method.delivery_tag)  # 任务完成，告诉客户端



if __name__ == '__main__':
    connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='rpc_queue')  # 声明一个rpc_queue ,

    channel.basic_qos(prefetch_count=1)
    # 在rpc_queue里收消息,收到消息就调用on_request
    channel.basic_consume(on_request, queue='rpc_queue')
    print(" [x] Awaiting RPC requests")
    channel.start_consuming()