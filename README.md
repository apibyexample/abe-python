# Api By Example for Python

This repository includes tools to be able to use the ABE format from within
Python code. In particular we aim to support python tests.


## Support for unittest.TestCase

You can use ABE in your unittests by mixing in `AbeTestMixin`, adding a
class-level attribute `samples_root` that points to a root folder containing
your sample files.

You can then compare how your code behaves re: an ABE sample with a simple
call:

```python
self.assert_matches_sample(
    path_to_sample, label, actual_url, actual_response
)
```


Here is a full example:


```python
import os

from abe.unittest import AbeTestMixin
from django.conf import settings
from django.core.urlresolvers import reverse
from rest_framework_jwt.test import APIJWTTestCase as TestCase

from ..factories.accounts import UserFactory, TEST_PASSWORD


class TestMyAccountView(AbeTestMixin, TestCase):
    url = reverse('myaccount')
    samples_root = os.path.join(settings.BASE_DIR, 'docs', 'api')

    def setUp(self):
        super(TestMyAccountView, self).setUp()
        self.user = UserFactory()

    def test_get_my_account_not_logged_in(self):
        """
        If I'm not logged in, I can't access any account data
        """
        response = self.client.get(self.url)
        self.assert_matches_sample(
            'accounts/profile.json', 'unauthenticated', self.url, response
        )

    def test_get_my_account_logged_in(self):
        """
        If I'm logged in, I can access any account data
        """
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

        response = self.client.get(self.url)

        self.assert_matches_sample(
            'accounts/profile.json', 'OK', self.url, response
        )
```

This is the file under `docs/api/accounts/profile.json`:

```json
{
    "description": "Retrieve profile of logged in user",
    "url": "/accounts/me",
    "method": "GET",
    "examples": {
        "OK": {
            "request": {
                "url": "/accounts/me"
            },
            "response": {
                "status": 200,
                "body": {
                    "id": 1,
                    "username": "user-0",
                    "first_name": "",
                    "last_name": "",
                    "email": "user-0@example.com"
                }
            }
        },
        "unauthenticated": {
            "description": "I am not logged in",
            "request": {
                "url": "/accounts/me"
            },
            "response": {
                "status": 403,
                "body": {
                    "detail": "Authentication credentials were not provided."
                }
            }
        }
    }
}
```
