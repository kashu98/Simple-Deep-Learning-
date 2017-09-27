import numpy as np

class Layer:
    def __init__(self, weight=None, bias=None):
        self.B = {'bias':bias, 'delta':None}
        self.X = {'input':None, 'output':None, 'shape':None, 'delta':None, 'batch':None, 'channel':None, 'hight':None, 'width':None}
        self.W = {'weight':weight, 'delta':None}
        if len(weight.shape) == 2:
            self.W['patch'], self.W['channel'] = 1,1
            self.W['hight'], self.W['width'] = weight.shape 
            #この場合hightが入力ノード数、widthが出力ノード数となる
        elif len(weight.shape) == 4:
            self.W['patch'], self.W['channel'], self.W['hight'], self.W['width'] = weight.shape 
    
    def __call__(self, weight, bias):    
        self.B['bias'] = bias
        self.W['weight'] = weight 
        if len(weight.shape) == 2:
            self.W['patch'], self.W['channel'] = 1,1
            self.W['hight'], self.W['width'] = weight.shape 
        elif len(weight.shape) == 4:
            self.W['patch'], self.W['channel'], self.W['hight'], self.W['width'] = weight.shape 

    def forward(self, X):
        self.X['input'] = X
        self.X['shape'] = X.shape
        if len(X.shape) == 2:
            self.X['hight'], self.X['channel'] = 1,1
            self.X['batch'], self.X['width'] = X.shape
        elif len(X.shape) == 4:
            self.X['batch'], self.X['channel'], self.X['hight'], self.X['width'] = X.shape


class Affine(Layer):
    """Affaine Layer (compatible with tensor) 
    """
    def __init__(self, weight=None, bias=None):
        super().__init__(weight, bias)

    def __call__(self, weight, bias):
        super().__call__(weight, bias)

    def forward(self, X):
        super().forward(X)
        self.X['output'] = self.X['input'].reshape(self.X['batch'],-1)
        return np.dot(self.X['output'], self.W['weight']) + self.B['bias']

    def backward(self, dY):
        self.W['delta'] = np.dot(self.X['output'].T, dY)
        self.B['delta'] = np.sum(dY, axis=0)
        return np.dot(dY, self.W['weight'].T).reshape(self.X['shape'])

class Convolutional(Layer):
    """Convolutional Layer
    """
    def __init__(self, filter=None, bias=None, stride=1, pad=0, pad_val=0):
        super().__init__(filter, bias)
        self.Y = {'hight':None, 'width':None}
        self.stride = stride
        self.pad = pad
        self.pad_val = pad_val

        self.x = None

    def __call__(self, filter, bias, stride=1, pad=0, pad_val=0):
        super().__init__(filter, bias)
        self.stride = stride
        self.pad = pad
        self.pad_val = pad_val

    def forward(self, X):
        super().forward(X)
        self.X['output'] = np.pad(self.X['input'], [(0,0), (0,0), (self.pad, self.pad), (self.pad, self.pad)], 'constant', constant_values=self.pad_val)
        self.Y['hight'] = (self.X['hight'] - self.W['hight'] + 2*self.pad)//self.stride + 1    
        self.Y['width'] = (self.X['width'] - self.W['width'] + 2*self.pad)//self.stride + 1

        self.x = np.zeros((self.X['batch'], self.Y['hight']*self.Y['width'], self.X['channel'], self.W['hight'], self.W['width']))
        for i in range(self.Y['hight']):
            for j in range(self.Y['width']):
                self.x[:,self.Y['width']*i + j,:,:,:] = self.X['output'][:,:,i*self.stride:i*self.stride + self.W['hight'],j*self.stride:j*self.stride + self.W['width']]
        self.x = self.x.reshape(self.X['batch'], self.Y['hight'], self.Y['width'], self.X['channel'], self.W['hight'], self.W['width'])
        return np.tensordot(self.x, self.W['weight'].transpose(1,2,3,0), axes=3).transpose(0,3,1,2) + self.B['bias']

    def forward2(self, X):
        #ベクトルの内積に落とし込む方法(.forward(X)推奨)
        super().forward(X)
        self.X['output'] = np.pad(self.X['input'], [(0,0), (0,0), (self.pad, self.pad), (self.pad, self.pad)], 'constant', constant_values=self.pad_val)
        self.Y['hight'] = (self.X['hight'] - self.W['hight'] + 2*self.pad)//self.stride + 1    
        self.Y['width'] = (self.X['width'] - self.W['width'] + 2*self.pad)//self.stride + 1

        self.x = np.zeros((self.X['batch'], self.Y['hight']*self.Y['width'], self.X['channel'], self.W['hight'], self.W['width']))
        for i in range(self.Y['hight']):
            for j in range(self.Y['width']):
                self.x[:,self.Y['width']*i + j,:,:,:] = self.X['output'][:,:,i*self.stride:i*self.stride + self.W['hight'],j*self.stride:j*self.stride + self.W['width']]
        col = self.x.reshape(self.X['batch']*self.Y['hight']*self.Y['width'], -1)
        row = self.W['weight'].reshape(self.W['patch'], -1).T
        Y = np.dot(col, row)
        return Y.reshape(self.X['batch'], self.Y['hight'], self.Y['width'], self.W['patch']).transpose(0,3,1,2)  + self.B['bias']

    def backward(self, dY):
        self.B['delta'] = np.sum(dY, axis=0)
        self.W['delta'] = np.tensordot(dY.transpose(1,0,2,3), self.x.reshape(self.X['batch'], self.Y['hight'], self.Y['width'], self.X['channel'], self.W['hight'], self.W['width']), axes=3)
        dx = np.tensordot(dY.transpose(0,2,3,1), self.W['weight'], axes=1).reshape(self.X['batch'], self.Y['hight']*self.Y['width'], self.X['channel'], self.W['hight'], self.W['width'])
        
        self.X['delta'] = np.zeros(self.X['shape'])
        for i in range(self.Y['hight']):
            for j in range(self.Y['width']):
                self.X['delta'][:,:,i*self.stride:i*self.stride + self.W['hight'],j*self.stride:j*self.stride + self.W['width']] += dx[:,self.Y['width']*i + j,:,:,:]
        return self.X['delta']

class Pooling(Layer):
    """Pooling Layer
    """
    def __init__(self, pool_hight=3, pool_width=3, stride=1, pad=0, pad_val=0):
        self.X = {'input':None, 'output':None, 'shape':None, 'delta':None, 'batch':None, 'channel':None, 'hight':None, 'width':None}
        self.Y = {'hight':None, 'width':None}
        self.pool = {'hight':pool_hight, 'width':pool_width}
        self.stride = stride
        self.pad = pad
        self.pad_val = pad_val

        self.x = None
        self.option = None

    def __call__(self, pool_hight, pool_width, stride=1, pad=0, pad_val=0):
        self.pool = {'hight':pool_hight, 'width':pool_width}
        self.stride = stride
        self.pad = pad
        self.pad_val = pad_val

    def forward(self, X, option=0):
        super().forward(X)
        self.option = option
        self.X['output'] = np.pad(self.X['input'], [(0,0), (0,0), (self.pad, self.pad), (self.pad, self.pad)], 'constant', constant_values=self.pad_val)
        self.Y['hight'] = (self.X['hight'] - self.pool['hight'] + 2*self.pad)//self.stride + 1    
        self.Y['width'] = (self.X['width'] - self.pool['width'] + 2*self.pad)//self.stride + 1
        self.x = np.zeros((self.X['batch'], self.Y['hight']*self.Y['width'], self.X['channel'], self.pool['hight'], self.pool['width']))
        for i in range(self.Y['hight']):
            for j in range(self.Y['width']):
                self.x[:,self.Y['width']*i + j,:,:,:] = self.X['output'][:,:,i*self.stride:i*self.stride + self.pool['hight'],j*self.stride:j*self.stride + self.pool['width']]
        self.X['output'] = self.x.reshape(self.X['batch'], self.Y['hight']*self.Y['width'], self.X['channel'], self.pool['hight']*self.pool['width'])
        if self.option == 0: # max pooloing
            self.x = np.max(self.X['output'], axis=3).transpose(0,2,1)
        elif self.option ==1: # average pooling
            self.x = np.average(self.X['output'], axis=3).transpose(0,2,1)
        return self.x.reshape(self.X['batch'], self.X['channel'], self.Y['hight'], self.Y['width'])

    def backward(self, dY):
        dY = dY.reshape(self.X['batch'], self.X['channel'],-1).transpose(0,2,1)
        dx = np.zeros((self.X['batch'], self.Y['hight']*self.Y['width'], self.X['channel'], self.pool['hight']*self.pool['width']))
        if self.option == 0:# max pooloing
            index = np.argmax(self.X['output'], axis=3).reshape(1,-1)[0]
            dY = dY.reshape(1,-1)[0]
            dx = dx.reshape(-1, self.pool['hight']*self.pool['width'])
            for i in range(len(index)):
                dx[i,index[i]] = dY[i]
        elif self.option ==1:# average pooling
            dY = dY.reshape(self.X['batch'], self.Y['hight']*self.Y['width'], self.X['channel'],1)
            dx = dx + dY
        
        dx = dx.reshape(self.X['batch'], self.Y['hight']*self.Y['width'], self.X['channel'], self.pool['hight'], self.pool['width'])
        self.X['delta'] =  np.zeros(self.X['shape'])
        for i in range(self.Y['hight']):
            for j in range(self.Y['width']):
                self.X['delta'][:,:,i*self.stride:i*self.stride + self.pool['hight'],j*self.stride:j*self.stride + self.pool['width']] += dx[:,self.Y['width']*i + j,:,:,:]
        return self.X['delta']

class Maxout(Layer):
    """Maxout layer (compatible with tensor) 
    weight: (input nodes, pooling number, output node)
    bias: (pooling number, output node)
    X: (batch number, nodes)
    Reference: http://proceedings.mlr.press/v28/goodfellow13.pdf
    """
    def __init__(self, weight=None, bias=None):
        super().__init__(weight, bias)
        self.W['patch'], self.W['hight'], self.W['width'] = weight.shape
        self.B['patch'], self.B['width'] = bias.shape
        self.Z = {'output':None, 'delta':None, 'batch':None, 'hight':None, 'width':None}
        self.A = {'output':None, 'delta':None}

    def __call__(self, weight, bias):
        super().__call__(weight, bias)
        self.W['patch'], self.W['hight'], self.W['width'] = weight.shape
        self.B['patch'], self.B['width'] = bias.shape

    def forward(self, X):
        super().forward(X)
        self.X['output'] = self.X['input'].reshape(self.X['batch'],-1)
        self.Z['output'] = np.tensordot(self.X['output'], self.W['weight'], axes=1) + self.B['bias']
        self.A['output'] = np.max(self.Z['output'], axis=2)
        return self.A['output']

    def backward(self, dY):
        self.Z['batch'], self.Z['hight'], self.Z['width'] = self.Z['output'].shape
        self.Z['delta'] = np.zeros_like(self.Z['output'])
        self.Z['delta'] = self.Z['delta'].reshape(-1, self.Z['width'])
        index = np.argmax(self.Z['output'], axis=2).reshape(1,-1)[0]
        dY = dY.reshape(1,-1)[0]
        for i in range(len(index)):
            self.Z['delta'][i, index[i]] = dY[i]
        self.Z['delta'] = self.Z['delta'].reshape(self.Z['batch'], self.Z['hight'], self.Z['width'])
        self.B['delta'] = np.sum(self.Z['delta'], axis=0)
        self.W['delta'] = np.tensordot(self.X['output'].T, self.Z['delta'], axes=1)
        self.X['delta'] = np.tensordot(self.Z['delta'], self.W['weight'].T, axes=2)
        self.X['delta'] = self.X['delta'].reshape(self.X['shape'])
        return self.X['delta']

class BatchNormalization(Layer):
    """Batch Normalizatoin Layer
    References: http://proceedings.mlr.press/v37/ioffe15.pdf
    """
    def __init__(self, gamma=None, beta=None, mean_predict=0, varience_predict=0.1):
        self.N = {'gamma':gamma, 'beta':beta, 'delta-gamma':None, 'delta-beta':None, 'mean':None, 'varience':None, 'delta-mean':None, 'delta-varience':None, 'delta-hat':None}
        self.X = {'input':None, 'output':None, 'shape':None, 'delta':None, 'batch':None, 'channel':None, 'hight':None, 'width':None}
        self.eps = 10e-7
        self.p_mean = mean_predict
        self.p_varience = varience_predict

    def __call__(self, gamma, beta, mean_predict=0, varience_predict=0.1):
        self.N['gamma'] = gamma
        self.N['beta'] = beta
        self.p_mean = mean_predict
        self.p_varience = varience_predict

    def forward(self, X):
        super().forward(X)
        self.N['mean'] = self.X['input'].mean(axis=0)
        self.N['variance'] = np.mean((self.X['input']-self.N['mean'])**2, axis=0)
        self.X['output'] = (self.X['input']-self.N['mean'])/np.sqrt(self.N['variance'] + self.eps)
        return self.N['gamma']*self.X['output'] + self.N['beta']
    
    def predict(self, X, mean, varience):
        self.p_mean = mean
        self.p_varience = varience
        self.X['output'] = (X - self.p_mean)/np.sqrt(self.p_varience + self.eps)
        return self.N['gamma']*self.X['output'] + self.N['beta']

    def backward(self, dY):
        self.N['delta-beta'] = np.sum(dY, axis=0)
        self.N['delta-gamma'] = np.sum(dY*self.X['output'], axis=0)
        self.N['delta-hat'] = dY*self.N['gamma']
        self.N['delta-varience'] = np.sum((-0.5)*self.N['delta-hat']*(self.X['input']-self.N['mean'])*(self.N['varience']+self.eps)**(-1.5), axis=0)
        self.N['delta-mean'] = np.sum((-1)*self.N['delta-hat']/np.sqrt(self.N['variance'] + self.eps),axis=0) - 2*self.N['delta-varience']*np.mean((self.X['input']-self.N['mean']), axis=0)
        self.X['delta'] = (-1)*self.N['delta-hat']/np.sqrt(self.N['variance'] + self.eps) + 2*self.N['delta-varience']*(self.X['input']-self.N['mean'])/self.X['batch'] + self.N['delta-mean']/self.X['batch']
        return self.X['delta']

class Dropout(Layer):
    """Dropout Layer
    全結合層
    """
    def __init__(self, dropout_rate=0.5):
        self.rate = dropout_rate
        self.mask = None    

    def __call__(self, dropout_rate=0.5):
        self.rate = dropout_rate

    def forward(self, X):
        self.mask = np.random.rand(*X.shape) < self.rate
        return X * self.mask
    
    def predict(self, X):
        return X * self.rate

    def backward(self, dY):
        return dY * self.mask
