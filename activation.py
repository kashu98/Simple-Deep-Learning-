import numpy as np
import sys

class Activation:
    def __init__(self):
        self.X = None
        self.Y = None
        self.sign = None
    def forward(self, X):
        self.X = X

class ReLU(Activation):
    """Rectified Linear Unit 
    """
    def __init__(self):
        super().__init__()
    def forward(self, X, α=0):
        self.sign = (X <= 0)
        X[self.sign] = X[self.sign] * α
        return X
    def backward(self, dY, α=0):
        dY[self.sign] = dY[self.sign] * α
        return dY

class LReLU(ReLU):
    """Leaky Rectified Linear Unit 
    """
    def __init__(self):
        super().__init__()
    def forward(self, X):
        return super().forward(X, 0.01)
    def backward(self, dY):
        return super().backward(dY, 0.01)

class PReLU(ReLU):
    """Parameteric Rectified Linear Unit
    """
    def __init__(self):
        super().__init__()
        self.α = None
    def forward(self, X, α):
        self.α = α
        return super().forward(X, α)
    def backward(self, dY):
        return super().backward(dY, self.α)

class ELU(Activation):
    """Exponential Linear Unit
    """
    def __init__(self):
        super().__init__()
        self.α = None
    def forward(self, X, α, λ=1.0):
        self.α = α
        X = λ * X
        self.sign = (X <= 0)
        X[self.sign] = α * (np.exp(X[self.sign]) - 1.0)
        self.Y = X
        return X
    def backward(self, dY, λ=1.0):
        dY = λ * dY
        dY[self.sign] = dY[self.sign] * (self.Y + self.α)
        return dY

class SELU(ELU):
    """Scaled Exponential Linear Unit (Klambauer et al., 2017)
    """
    def __init__(self):
        super().__init__() 
        self.α = 1.67326
        self.λ = 1.0507
    def forward(self, X):
        return super().forward(X, self.α, self.λ)
    def backward(self, dY):
        return super().backward(dY, self.λ)

class Sigmoid(Activation):
    """Logistic Function
    """
    def __init__(self):
        super().__init__()
    def forward(self, X):
        self.Y = 1/(1 + np.exp(-X))
        return self.Y
    def backward(self, dY):
        dX = dY * self.Y * (1.0 - self.Y)
        return dX

class SoftPlus(Sigmoid):
    """
    """
    def __init__(self):
        super().__init__()
    def forward(self, X):
        self.X = X
        return np.log(1.0 + np.exp(X))
    def backward(self, dY):
        dX = dY * super().forward(self.X)
        return dX

class Tanh(Activation):
    """
    """
    def __init__(self):
        super().__init__()
    def forward(self, X):
        self.Y = 2.0/(1.0 + np.exp(-2 * X) - 1.0)
        return self.Y
    def backward(self, dY):
        dX = dY * (1.0 - (self.Y)**2)
        return dX

class ArcTan(Activation):
    """
    """
    def __init__(self):
        super().__init__()
    def forward(self, X):
        self.X = X
        return np.arctan(X)
    def backward(self, dY):
        dX = dY/(1.0 + (self.X)**2)
        return dX

class SoftSign(Activation):
    """
    """
    def __init__(self):
        super().__init__()
    def forward(self, X):
        self.sign = (X < 0)
        aX = X.copy()
        aX[self.sign] = -1.0 * aX[self.sign]
        self.X = aX
        return X/(1.0 + aX)
    def backward(self, dY):
        return dY/(1.0 + self.X)**2 

def Softmax(X):
    option = X.ndim
    if option == 1:
        X = X - np.max(X)
        return np.exp(X) / np.sum(np.exp(X))
    elif option == 2:
        X = X.T
        X = X - np.max(X, axis=0)
        Y = np.exp(X) / np.sum(np.exp(X), axis=0)
        return Y.T
    else:
        sys.stderr.write('unexpected dimention data was given to Softmax function.')    
