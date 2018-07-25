# aquarius


```python
from server import Aquarius


app = Aquarius(__name__)


@app.router
def test(request):
    return request.to_response("Hello Word")

app.run()
```
![Image text](https://github.com/AquariusMr/aquarius/blob/master/img-test/test.png)