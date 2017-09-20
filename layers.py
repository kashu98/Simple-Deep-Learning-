import numpy as np

class Layer:
    def __init__(self, weight, bias):
        self.B = {'bias':bias, 'delta':None}
        self.X = {'input':None, 'output':None, 'shape':None, 'delta':None, 'batch':None, 'channel':None, 'hight':None, 'width':None}
        self.W = {'weight':weight, 'delta':None}
        if len(weight.shape) == 2:
            self.W['patch'], self.W['channel'] = 1,1
            self.W['hight'], self.W['width'] = weight.shape 
            #この場合hightが入力ノード数、widthが出力ノード数となる
        elif len(weight.shape) == 4:
            self.W['patch'], self.W['channel'], self.W['hight'], self.W['width'] = weight.shape 
    
    def foward(self, X):
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
    def __init__(self, weight, bias):
        super().__init__(weight, bias)

    def foward(self, X):
        super().foward(X)
        self.X['output'] = self.X['input'].reshape(self.X['batch'],-1)
        return np.dot(self.X['output'], self.W['weight']) + self.B['bias']

    def backward(self, dY):
        self.W['delta'] = np.dot(self.X['output'].T, dY)
        self.B['delta'] = np.sum(dY, axis=0)
        return np.dot(dY, self.W['weight'].T).reshape(self.X['shape'])

class Convolutional(Layer):
    """Convolutional Layer
    """
    def __init__(self, filter, bias, stride=1, pad=0, pad_val=0):
        super().__init__(filter, bias)
        self.Y = {'hight':None, 'width':None}
        self.stride = stride
        self.pad = pad
        self.pad_val = pad_val

        self.x = None
    
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

    def __forward(self, X):
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
