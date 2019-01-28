import re

from puppy_interactions.interactions.models import Interaction

# create pattern components
uid = r'<@[\da-zA-Z]+(|[^>])?>'
raw_name = r'[a-zA-Z]+(\W[a-zA-Z]+)?'
rating = '\{}|{}'.format(Interaction.POSITIVE, Interaction.NEGATIVE)
uid_block = rf"(({uid})+\W?({rating})+)"
raw_name_block = rf"(({raw_name})+\W?({rating})+)"
multi_block = r'({}|{})'.format(uid_block, raw_name_block)

# logs_pattern components
days = '[\d]+'
aggregate = 'person|time'
filter = rating

c_str = r'{}(\W{})*'.format(multi_block, multi_block)
create_pattern = re.compile(c_str, re.IGNORECASE)
interaction_pattern = re.compile(multi_block)

l_str = r'^({})?(\W?({}))?(\W?({}))?$'.format(days, aggregate, filter)
logs_pattern = re.compile(l_str, re.IGNORECASE)
days_pattern = re.compile(days)
aggregate_pattern = re.compile(aggregate, re.I)
filter_pattern = re.compile(filter, re.I)

clear_pattern = re.compile(r'^clear$', re.IGNORECASE)
help_pattern = re.compile(r'^help$', re.IGNORECASE)
