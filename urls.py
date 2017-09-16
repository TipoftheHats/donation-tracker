from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    'tracker.views',
    url(r'^bids/(?P<event>\w+|)$', 'bidindex'),
    url(r'^bid/(?P<id>-?\d+)$', 'bid'),
    url(r'^donors/(?P<event>\w+|)$', 'donorindex'),
    url(r'^donor/(?P<id>-?\d+)$', 'donor'),
    url(r'^donor/(?P<id>-?\d+)/(?P<event>\w*)$', 'donor'),
    url(r'^donations/(?P<event>\w+|)$', 'donationindex'),
    url(r'^donation/(?P<id>-?\d+)$', 'donation'),
    url(r'^runs/(?P<event>\w+|)$', 'runindex'),
    url(r'^run/(?P<id>-?\d+)$', 'run'),
    url(r'^prizes/(?P<event>\w+|)$', 'prizeindex'),
    url(r'^prize/(?P<id>-?\d+)$', 'prize'),
    url(r'^prize_donors$', 'prize_donors'),
    url(r'^draw_prize$', 'draw_prize'),
    url(r'^merge_schedule/(?P<id>-?\d+)$', 'merge_schedule'),
    url(r'^events/$', 'eventlist'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^search/$', 'search'),
    url(r'^add/$', 'add'),
    url(r'^edit/$', 'edit'),
    url(r'^delete/$', 'delete'),
    url(r'^command/$', 'command'),
    url(r'^me/$', 'me'),
    url(r'^api/v1/$', 'api_v1'),
    url(r'^api/v1/search/$', 'search'),
    url(r'^api/v1/add/$', 'add'),
    url(r'^api/v1/edit/$', 'edit'),
    url(r'^api/v1/delete/$', 'delete'),
    url(r'^api/v1/command/$', 'command'),
    url(r'^api/v1/me/$', 'me'),
    url(r'^api/v2/', include('tracker.api.urls')),
    url(r'^index/(?P<event>\w+|)$', 'index', name='index'),
    url(r'^donate/(?P<event>\w+)$', 'donate', name='donate'),
    # unfortunately, using the 'word' variant here clashes with the admin site (not to mention any unparameterized urls), so I guess its going to have to be this way for now.  I guess that ideally, one would only use the 'index' url, and redirect to it as neccessary).
    url(r'^(?P<event>\d+|)$', 'index'),
    url(r'^paypal_return/$', 'paypal_return', name='paypal_return'),
    url(r'^paypal_cancel/$', 'paypal_cancel', name='paypal_cancel'),
    url(r'^ipn/$', 'ipn', name='ipn'),
    url(r'^disconnect_steam/$', 'disconnect_steam', name='disconnect_steam'),
    url(r'^admin/refresh_schedule/$', 'refresh_schedule'),  # ugly hack: has to be here or we get auth intercepted
    url(r'^user/index/$', 'user_index', name='user_index'),
    url(r'^user/user_prize/(?P<prize>\d+)$', 'user_prize', name='user_prize'),
    url(r'^user/prize_winner/(?P<prize_win>\d+)$', 'prize_winner', name='prize_winner'),
    url(r'^user/submit_prize/(?P<event>\w+)$', 'submit_prize', name='submit_prize'),
    url(r'^user/login/$', 'login', name='login'),
    url(r'^user/logout/$', 'logout', name='logout'),
    url(r'^user/password_reset/$', 'password_reset', name='password_reset'),
    url(r'^user/password_reset_done/$', 'password_reset_done', name='password_reset_done'),
    url(r'^user/password_reset_confirm/$', 'password_reset_confirm', name='password_reset_confirm'),
    url(r'^user/password_reset_complete/$', 'password_reset_complete', name='password_reset_complete'),
    url(r'^user/password_change/$', 'password_change', name='password_change'),
    url(r'^user/password_change_done/$', 'password_change_done', name='password_change_done'),
    url(r'^user/register/$', 'register', name='register'),
    url(r'^user/confirm_registration/$', 'confirm_registration', name='confirm_registration'),

    url('', include('social_django.urls', namespace='social')),
)
