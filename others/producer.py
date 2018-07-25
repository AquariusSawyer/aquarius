import pika
import uuid
import time
import json

import datetime


tast_list = []


class AquariusRpcClient(object):

    def __init__(self):

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)

        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response,  # 只要一收到消息就调用on_response
                                   no_ack=True,
                                   queue=self.callback_queue)  # 收这个queue的消息

    def on_response(self, ch, method, props, body):  # 必须四个参数

        # 如果收到的ID和本机生成的相同，则返回的结果就是我想要的指令返回的结果
        if self.corr_id == props.correlation_id:
            self.response = body

    def rpc_task(self, func_name, *args, **kwargs):

        body = {
            "func": func_name,
            "args": args,
            "kwargs": kwargs,
        }

        self.corr_id = str(uuid.uuid4())

        body = json.dumps(body)


        self.response = None

        self.channel.basic_publish(
                exchange='',
                routing_key='rpc_queue',  # 发消息到rpc_queue
                properties=pika.BasicProperties(  # 消息持久化
                    reply_to = self.callback_queue,  # 让服务端命令结果返回到callback_queue
                    correlation_id = self.corr_id,  # 把随机uuid同时发给服务器
                ),
                body=body
        )

        tast_list.append(self)


if __name__ == '__main__':

    fibonacci_rpc = AquariusRpcClient()

    fibonacci_rpc.rpc_task("add", 3, 234, c=2)

    fibonacci_rpc.rpc_task("add", 3, 234, c=2)


    while len(tast_list):

            for i ,task in enumerate(tast_list):

                task.connection.process_data_events()

                if task.response:
                    print(task.response.decode("utf-8"), datetime.datetime.now())
                    tast_list.pop(i)
