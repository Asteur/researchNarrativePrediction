import six, pickle
from sklearn.pipeline import Pipeline
from keras.models import load_model
import transformer
from transformer import *
from classifier import *


# def load_pipeline(filepath, embeddings=None):    
#     #load saved models
#     if os.path.is
#     with open(filepath + '/transformer.pkl', 'rb') as f:
#         transformer = pickle.load(f)
#     if embeddings is not None:
#         #if embeddings are given, add them to transformer (they don't come pickled with transformer)
#         transformer.word_embeddings = embeddings
#         transformer.n_embedding_nodes = embeddings.vector_size
#     else:
#         transformer.word_embeddings = None

#     return transformer, classifier

class RNNPipeline(Pipeline):
    #sklearn pipeline won't pass extra parameters other than input data between steps
    def _pre_transform(self, X, y_seqs=None, **fit_params):
        fit_params_steps = dict((step, {}) for step, _ in self.steps)
        for pname, pval in six.iteritems(fit_params):
            step, param = pname.split('__', 1)
            fit_params_steps[step][param] = pval
        Xt = X
        for name, transform in self.steps[:-1]:
            if hasattr(transform, "fit_transform"):
                Xt, y_seqs, rnn_params = transform.fit_transform(Xt, y_seqs, **fit_params_steps[name])
            else:
                Xt, y_seqs, rnn_params = transform.fit(Xt, y_seqs, **fit_params_steps[name]).transform(Xt, y_seqs)
        return Xt, y_seqs, rnn_params, fit_params_steps[self.steps[-1][0]]
    def fit(self, X, y=None, y_seqs=None, **fit_params):
        if self.steps[-1][-1].__class__.__name__ == 'RNNLM' and\
            self.steps[0][-1].__class__.__name__ == 'SequenceTransformer' and\
            self.steps[0][-1].get_params()['word_embeddings'] is not None:
            #import pdb;pdb.set_trace()
            #if this is a language model, no explicit output; input will be copied to output before embedding,
            #if input is embedded
            self.steps[0][-1].set_params(copy_input_to_output = True)
        # if self.steps[-1][-1].__class__.__name__ in ['Seq2SeqClassifier', 'MergeSeqClassifier',
        #                                               'RNNLMClassifier', 'RNNLM', 'SeqBinaryClassifier']:
        Xt, y_seqs, rnn_params, fit_params = self._pre_transform(X, y_seqs, **fit_params)
        # else:
        #     Xt, _, rnn_params, fit_params = self._pre_transform(X, y_seqs, **fit_params)
        if self.steps[-1][-1].__class__.__name__ == 'RNNLM':
            self.steps[-1][-1].fit_epoch(Xt, y_seqs, rnn_params, **fit_params)
        elif self.steps[-1][-1].__class__.__name__ == 'SeqBinaryClassifier':
            self.steps[-1][-1].fit(Xt, y, y_seqs, rnn_params, **fit_params)
        else:
            self.steps[-1][-1].fit(Xt, y, rnn_params, **fit_params)
        return self
    def predict(self, X, y=None, y_seqs=None, **kwargs):
        #if choice sequences given, predict sequence from this list
        #import pdb;pdb.set_trace()
        Xt = X
        for name, transform in self.steps[:-1]:
            Xt, y_seqs = transform.transform(Xt, y_seqs)
        if y_seqs is not None and y is not None:
            return self.steps[-1][-1].predict(Xt, y, y_seqs, **kwargs)
        elif y_seqs is not None:
            return self.steps[-1][-1].predict(Xt, y_seqs, **kwargs)
        else:
            return self.steps[-1][-1].predict(Xt, **kwargs)
    def encode(self, X, **kwargs):
        Xt = X
        for name, transform in self.steps[:-1]:
            Xt, _ = transform.transform(Xt)
        return self.steps[-1][-1].encode(Xt, **kwargs)


class AutoencoderPipeline(Pipeline):
    #sklearn pipeline won't pass extra parameters other than input data between steps
    def _pre_transform(self, X, y_seqs=None, **fit_params):
        fit_params_steps = dict((step, {}) for step, _ in self.steps)
        for pname, pval in six.iteritems(fit_params):
            step, param = pname.split('__', 1)
            fit_params_steps[step][param] = pval
        Xt = X
        for name, transform in self.steps[:-1]:
            Xt, y_seqs = transform.fit(Xt, y_seqs, **fit_params_steps[name]).transform(Xt, y_seqs)
        return Xt, y_seqs, fit_params_steps[self.steps[-1][0]]
    def fit(self, X, y=None, y_seqs=None, **fit_params):
        #import pdb;pdb.set_trace()
        Xt, y, fit_params = self._pre_transform(X, y_seqs, **fit_params)
        self.steps[-1][-1].fit(Xt, y, **fit_params)
        return self
    def predict(self, X, y_choices=None):
        #check if y_choices is single set or if there are different choices for each input
        
        #import pdb;pdb.set_trace()
        Xt = X
        for name, transform in self.steps[:-1]:
            Xt, y_choices = transform.transform(Xt, y_choices)
        if y_choices is not None:
            return self.steps[-1][-1].predict(Xt, y_choices)
        else:
            return self.steps[-1][-1].predict(Xt)