# mod = __import__('bclib', fromlist=['edge'])
# print(mod)
# edge = getattr(mod, 'edge')
# print(edge.__version__)


# mod = __import__('bclib', fromlist=['edge'])
# print(mod)
# edge = getattr(mod, 'edge')
# print(edge.__version__)

########################
# import asyncio
# import signal


# class GracefulExit(SystemExit):
#     code = 1


# def raise_graceful_exit(*args):
#     print("sdsdsds")
#     loop.stop()
#     print("Gracefully shutdown")
#     raise GracefulExit()


# def do_something():
#     while True:
#         pass


# loop = asyncio.get_event_loop()
# signal.signal(signal.SIGINT, raise_graceful_exit)
# signal.signal(signal.SIGTERM, raise_graceful_exit)

# try:
#     loop.run_forever(do_something())
# except GracefulExit:
#     pass
# finally:
#     loop.close()
##################


import time
import asyncio


# async def main():
#     print(f'{time.ctime()} Hello!')
#     await asyncio.sleep(1.0)
#     print(f'{time.ctime()} Goodbye!')


# def blocking():
#     time.sleep(0.5)
#     print(f"{time.ctime()} Hello from a thread!")


# loop = asyncio.get_event_loop()
# task = loop.create_task(main())
# loop.run_in_executor(None, blocking)
# loop.run_until_complete(task)
# pending = asyncio.all_tasks(loop=loop)
# for task in pending:
#     task.cancel()
# group = asyncio.gather(*pending, return_exceptions=True)
# loop.run_until_complete(group)
# loop.close()
###########################
# async def main():
#     print(f'{time.ctime()} Hello!')
#     await asyncio.sleep(1.0)
#     # pending = asyncio.all_tasks()
#     # print(len(pending))
#     # p, *_ = pending
#     # p.__haha = 12
#     # print(p)
#     print(f'{time.ctime()} Goodbye!')

# asyncio.run(main())
# print("hi")

# loop = asyncio.get_event_loop()
# task = loop.create_task(main())

# for i in range(1000000000):
#     i = i+1
#     pass
# print("sdsds")
# loop.run_until_complete(task)
# pending = asyncio.all_tasks(loop=loop)
# #print(len(pending), task.__haha)
# for item in pending:
#     item.cancel()

# group = asyncio.gather(*pending, return_exceptions=True)
# loop.run_until_complete(group)
# loop.close()

# print("hi")
################


# async def p(task: asyncio.Task):
#     await asyncio.sleep(1)
#     try:
#         task.set_result(asyncio.CancelledError())
#     except Exception as ex:
#         print(ex)
#         task.cancel()


# async def f():
#     try:
#         while True:
#             await asyncio.sleep(0)
#     except asyncio.CancelledError:
#         print('I was cancelled!')
#     except StopIteration:
#         return (6)
#     else:
#         return (111)

# loop = asyncio.get_event_loop()
# task1 = loop.create_task(f())
# task2 = loop.create_task(p(task1))

# loop.run_until_complete(task1)
# #t = asyncio.gather(task1, task2)
# # asyncio.run(t)
# print('r')

####

# async def p(task: asyncio.Future):
#     await asyncio.sleep(3)
#     try:
#         task.set_result(12)
#     except Exception as ex:
#         print(ex)
#         task.cancel()


# f = asyncio.Future()


# async def ll():
#     print("ff", await f)

# loop = asyncio.get_event_loop()
# task1 = loop.create_task(p(f))
# task2 = loop.create_task(ll())

# loop.run_until_complete(task2)
# loop.run_until_complete(f)
# print(f.result())
# #t = asyncio.gather(task1, task2)
# # asyncio.run(t)
# print('r')

###

# async def f(delay):
#     await asyncio.sleep(delay)
# loop = asyncio.get_event_loop()
# t1 = loop.create_task(f(1))
# t2 = loop.create_task(f(2))
# loop.run_until_complete(t1)
# loop.close()

#####
# async def main():
#     loop = asyncio.get_running_loop()
#     loop.run_in_executor(None, blocking)
#     print(f'{time.ctime()} Hello!')
#     await asyncio.sleep(1.0)
#     print(f'{time.ctime()} Goodbye!')


# def blocking():
#     time.sleep(1.5)
#     print(f"{time.ctime()} Hello from a thread!")


# asyncio.run(main())
########

# token = asyncio.Future()


# async def new(name: str, time: int = 0):
#     try:
#         if time == 0:
#             while not token.done():
#                 print(f"{name} task run...")
#                 await asyncio.sleep(1)
#         else:
#             print(f"{name} task run...")
#             await asyncio.sleep(time)
#             print(f"{name} task run...")
#     except asyncio.CancelledError:
#         print(f"{name} task cancel")


# def old(name: str):
#     try:
#         while not token.done():
#             print(f"{name} task(old) run...")
#             time.sleep(1)
#     except asyncio.CancelledError:
#         print(f"{name} task cancel")


# async def token_hadler():
#     await asyncio.sleep(3)
#     token.set_result(0)
# # asyncio.set_event_loop(asyncio.get_event_loop())
# # t = asyncio.get_running_loop()

# loop = asyncio.get_event_loop()


# # print(t is loop)


# t1 = loop.create_task(new("new1", 3))
# t2 = loop.create_task(new("new2"))
# t3 = loop.create_task(new("new3"))
# t4 = loop.create_task(new("new4"))
# loop.create_task(token_hadler())
# l = loop.run_in_executor(None, old, "old1")
# loop.run_until_complete(t1)
# l.cancel()

# loop.close()
# # pending = asyncio.all_tasks(loop=loop)
# # for task in pending:
# #     task.cancel()
# # group = asyncio.gather(*pending, return_exceptions=True)
# # loop.run_until_complete(group)
# # loop.close()
# print('end')


######
async def f(delay):
    try:
        await asyncio.sleep(delay)
        print(delay)
    except asyncio.CancelledError:
        print("sdsds")


async def f1(delay):
    try:
        await asyncio.sleep(delay)
        print(delay)
    except asyncio.CancelledError:
        print("sdsds")


def ff():
    try:
        time.sleep(30)
    except StopIteration:
        print("1")


loop = asyncio.get_event_loop()
t1 = loop.create_task(f1(1))
t2 = loop.create_task(f(200))
loop.run_until_complete(t1)
t2.cancel()
loop.run_until_complete(t2)
loop.close()
#####
# p: asyncio.Future


# async def f(delay):
#     try:
#         await asyncio.sleep(2)
#         p.cancel()
#         print(delay)
#         await asyncio.sleep(delay)
#         print(delay)
#     except asyncio.CancelledError:
#         print("sdsds")


# def ff():
#     while True:
#         time.sleep(1)
#         print('sds')


# loop = asyncio.get_event_loop()
# p = loop.run_in_executor(None, ff)
# t1 = loop.create_task(f(100))
# try:
#     loop.run_until_complete(p)
# except StopIteration:
#     print("1")
# except asyncio.CancelledError:
#     print("e sdsds")
# print("d")
# loop.run_until_complete(t1)

# loop.close()
######
# import asyncio
# from signal import SIGINT, SIGTERM


# async def main():
#     try:
#         while True:
#             print('<Your app is running>')
#             await asyncio.sleep(1)
#     except asyncio.CancelledError:
#         for i in range(3):
#             print('<Your app is shutting down...>')
#             await asyncio.sleep(1)


# def handler(sig):
#     loop.stop()
#     print(f'Got signal: {sig!s}, shutting down.')
#     loop.remove_signal_handler(SIGTERM)
#     loop.add_signal_handler(SIGINT, lambda: None)


# loop = asyncio.get_event_loop()
# for sig in (SIGTERM, SIGINT):
#     loop.add_signal_handler(sig, handler, sig)

# loop.create_task(main())
# loop.run_forever()
# tasks = asyncio.all_tasks(loop=loop)
# for t in tasks:
#     t.cancel()
# group = asyncio.gather(*tasks, return_exceptions=True)
# loop.run_until_complete(group)
# loop.close()
###############
# import asyncio
# import signal


# async def main():
#     try:
#         i = 0
#         while i < 10:
#             print('<Your app is running>')
#             await asyncio.sleep(1)
#             i += 1
#     except asyncio.CancelledError:
#         for i in range(3):
#             print('<Your app is shutting down...>')
#             await asyncio.sleep(1)

# if __name__ == '__main__':

#     class GracefulExit(SystemExit):
#         code = 1

#     def raise_graceful_exit(*args):
#         tasks = asyncio.all_tasks(loop=loop)
#         for t in tasks:
#             t.cancel()

#         loop.stop()
#         print("Gracefully shutdown")
#         raise GracefulExit()

#     def do_something():
#         while True:
#             pass

#     loop = asyncio.get_event_loop()
#     signal.signal(signal.SIGINT,  raise_graceful_exit)
#     signal.signal(signal.SIGTERM, raise_graceful_exit)
#     task = loop.create_task(main())
#     try:
#         loop.run_until_complete(task)
#     except GracefulExit:
#         print('Got signal: SIGINT, shutting down.')
#     if 1:
#         tasks = asyncio.all_tasks(loop=loop)
#         for t in tasks:
#             t.cancel()
#         group = asyncio.gather(*tasks, return_exceptions=True)
#         loop.run_until_complete(group)
#         loop.close()
####

# import signal


# async def main(name: int):
#     if name < 3:
#         asyncio.get_running_loop().create_task(main(name+1))
#     try:

#         while True:
#             print(f'<Your {name} app is running>')
#             await asyncio.sleep(1)
#     except asyncio.CancelledError:
#         for _ in range(name):
#             print(f'<Your {name} app is shutting down...>')
#             await asyncio.sleep(1)


# def blocking():
#     for i in range(7):
#         print('b', i)
#         time.sleep(1)


# async def wrapper(future):
#     try:
#         await future
#     except asyncio.CancelledError:
#         print("sdsd")
#         await future


# loop = asyncio.get_event_loop()

# for sig in (signal.SIGTERM, signal.SIGINT):
#     signal.signal(sig, lambda sig, _: loop.stop())

# fut = loop.run_in_executor(None, blocking)
# loop.create_task(wrapper(fut))
# loop.create_task(main(1))
# loop.run_forever()
# tasks = asyncio.all_tasks(loop=loop)
# for t in tasks:
#     t.cancel()
# group = asyncio.gather(*tasks, return_exceptions=True)
# loop.run_until_complete(group)
# loop.close()
# print("close")
