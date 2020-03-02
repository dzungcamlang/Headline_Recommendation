# -*- coding: UTF-8 -*-

from server import cache_client
import logging
from datetime import datetime

logger = logging.getLogger('recommend')


def get_cache_from_redis_hbase(temp, hbu, redis_cache_len=100):
    """
    读取用户的缓存结果
    :temp param: 用户请求参数
    :hbu param: hbase 读取
    """
    # 1、redis 8 号数据库读取
    key = 'reco:{}:{}:art'.format(temp.user_id, temp.channel_id)
    res = cache_client.zrevrange(key, 0, temp.article_num - 1)
    if res:
        cache_client.zrem(key, *res) # 删除取出的数据
    else:
        # 2、redis没有数据，进行wait_recommend读取，放入redis中
        cache_client.delete(key)
        try:
            hbase_cache = eval(hbu.get_table_row('wait_recommend',
                                                 'reco:{}'.format(temp.user_id).encode(),
                                                 'channel:{}'.format(temp.channel_id).encode()))
        except Exception as e:
            logger.warning("{} WARN read user_id:{} wait_recommend exception:{} not exist".format(
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), temp.user_id, e))
            hbase_cache = []

        # 如果hbase_cache为Null，则直接返回
        if not hbase_cache:
            return hbase_cache

        if len(hbase_cache) > redis_cache_len:
            logger.info(
                "{} INFO reduce cache  user_id:{} channel:{} wait_recommend data".format(
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), temp.user_id, temp.channel_id))

            # 截取的数据放入Redis
            redis_cache = hbase_cache[:redis_cache_len]
            cache_client.zadd(key, dict(zip(redis_cache, range(len(redis_cache)))))
            # 剩下的数据重新放回到HBASE的wait_recommend。
            hbu.get_table_put('wait_recommend',
                              'reco:{}'.format(temp.user_id).encode(),
                              'channel:{}'.format(temp.channel_id).encode(),
                              str(hbase_cache[redis_cache_len:]).encode(),
                              timestamp=temp.time_stamp)
        else:
            logger.info(
                "{} INFO delete user_id:{} channel:{} wait_recommend cache data".format(
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), temp.user_id, temp.channel_id))
            # 数据放入Redis
            cache_client.zadd(key, dict(zip(hbase_cache, range(len(hbase_cache)))))
            # 清空HBASE的数据
            hbu.get_table_put('wait_recommend',
                              'reco:{}'.format(temp.user_id).encode(),
                              'channel:{}'.format(temp.channel_id).encode(),
                              str([]).encode(),
                              timestamp=temp.time_stamp)

        # 取出刚刚存储到Redis的数据
        res = cache_client.zrevrange(key, 0, temp.article_num - 1)
        if res:
            cache_client.zrem(key, *res) # 删除取出数据


    # 存进历史推荐表当中
    res = list(map(int, res))

    logger.info("{} INFO get cache data and store user_id:{} channel:{} cache data".format(
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'), temp.user_id, temp.channel_id))

    # 3、推荐出去的结果放入历史结果
    # 直接写入历史记录当中，表示这次又成功推荐一次
    hbu.get_table_put('history_recommend',
                           'reco:his:{}'.format(temp.user_id).encode(),
                           'channel:{}'.format(temp.channel_id).encode(),
                           str(res).encode(),
                           timestamp=temp.time_stamp)

    return res