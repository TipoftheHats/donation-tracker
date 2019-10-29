import _ from 'underscore';

import Cookies from '../../util/cookies';
import HTTPUtil from '../../util/http';


function onModelStatusLoad(model) {
    return {
        type: 'MODEL_STATUS_LOADING', model
    };
}

function onModelStatusSuccess(model) {
    return {
        type: 'MODEL_STATUS_SUCCESS', model
    };
}

function onModelStatusError(model) {
    return {
        type: 'MODEL_STATUS_ERROR', model
    };
}

function onModelCollectionReplace(model, models) {
    return {
        type: 'MODEL_COLLECTION_REPLACE', model, models
    };
}

function onModelCollectionAdd(model, models) {
    return {
        type: 'MODEL_COLLECTION_ADD', model, models
    };
}

function onModelCollectionRemove(model, models) {
    return {
        type: 'MODEL_COLLECTION_REMOVE', model, models
    };
}

// TODO: Better solution than this
const modelTypeMap = {
    speedrun: 'run'
};

function loadModels(model, params, additive) {
  return (dispatch) => {
    dispatch(onModelStatusLoad(model));
    return HTTPUtil.get(`${API_ROOT}search`, {
      ...params,
      type: modelTypeMap[model] || model,
    }).then((models) => {
      dispatch(onModelStatusSuccess(model));
      const action = additive ? onModelCollectionAdd : onModelCollectionReplace;
      dispatch(action(model,
        models.reduce((acc, v) => {
          if (v.model.toLowerCase() === `tracker.${model}`.toLowerCase()) {
            v.fields.pk = v.pk;
            acc.push(v.fields);
          }
          return acc;
        }, [])
      ));
    }).catch((error) => {
      dispatch(onModelStatusError(model));
      if(!additive) {
        dispatch(onModelCollectionReplace(model, []));
      }
    });
  }
}

function onNewDraftModel(model) {
    return {
        type: 'MODEL_NEW_DRAFT', model
    };
}

function newDraftModel(model) {
    return (dispatch) => {
        dispatch(onNewDraftModel(model));
    };
}

function onDeleteDraftModel(model) {
    return {
        type: 'MODEL_DELETE_DRAFT', model
    }
}

function deleteDraftModel(model) {
    return (dispatch) => {
        dispatch(onDeleteDraftModel(model));
    };
}

function onDraftModelUpdateField(model, pk, field, value) {
    return {
        type: 'MODEL_DRAFT_UPDATE_FIELD', model, pk, field, value
    };
}

function updateDraftModelField(model, pk, field, value) {
    return (dispatch) => {
        dispatch(onDraftModelUpdateField(model, pk, field, value));
    };
}

function onSetInternalModelField(model, pk, field, value) {
    return {
        type: 'MODEL_SET_INTERNAL_FIELD', model, pk, field, value
    };
}

function setInternalModelField(model, pk, field, value) {
    return (dispatch) => {
        dispatch(onSetInternalModelField(model, pk, field, value));
    };
}

function onSaveDraftModelError(model, error, fields) {
    return {
        type: 'MODEL_SAVE_DRAFT_ERROR', model, error, fields
    };
}

function saveDraftModels(models) {
    return (dispatch) => {
        _.each(models, (model) => {
            dispatch(setInternalModelField(model.type, model.pk, 'saving', true));
            const url = model.pk < 0 ? `${API_ROOT}add/` : `${API_ROOT}edit/`;

            HTTPUtil.post(url, {
                type: modelTypeMap[model.type] || model.type,
                id: model.pk,
                ..._.omit(model.fields, (v, k) => k.startsWith('_'))
            }, {
                encoder: HTTPUtil.Encoders.QUERY,
            }).then((savedModels) => {
                const models = savedModels.reduce((acc, v) => {
                    if (v.model.toLowerCase() === `tracker.${model.type}`.toLowerCase()) {
                        v.fields.pk = v.pk;
                        acc.push(v.fields);
                    } else {
                        console.warn('unexpected model', v);
                    }
                    return acc;
                }, []);
                dispatch(onModelCollectionAdd(model.type, models));
                dispatch(onDeleteDraftModel(model));
            }).catch((response) => {
                const json = response.json();
                dispatch(onSaveDraftModelError(model, json ? json.error : response.body(), json ? json.fields : {}));
            }).finally(() => {
                dispatch(setInternalModelField(model.type, model.pk, 'saving', false));
            });
        });
    }
}

function saveField(model, field, value) {
    return (dispatch) => {
        if (model.pk) {
            dispatch(setInternalModelField(model.type, model.pk, 'saving', true));
            if (value === undefined || value === null) {
                value = 'None';
            }
            HTTPUtil.post(`${API_ROOT}edit/`, {
                type: modelTypeMap[model.type] || model.type,
                id: model.pk,
                [field]: value
            }, {
              encoder: HTTPUtil.Encoders.QUERY
            }).then((savedModels) => {
                dispatch(onModelCollectionAdd(model.type,
                    savedModels.reduce((o, v) => {
                        if (v.model.toLowerCase() === `tracker.${model.type}`.toLowerCase()) {
                            v.fields.pk = v.pk;
                            o.push(v.fields);
                        } else {
                            console.warn('unexpected model', v);
                        }
                        return o;
                    }, [])
                ));
            }).catch((response) => {
                const json = response.json();
                dispatch(onSaveDraftModelError(model, json ? json.error : response.body(), json ? json.fields : {}));
            }).finally(() => {
                dispatch(setInternalModelField(model.type, model.pk, 'saving', false));
            });
        }
    }
}

function command(command) {
    return (dispatch) => {
        return HTTPUtil.post(`${API_ROOT}command/`, {
            data: JSON.stringify({
                command: command.type,
                ...command.params,
            }),
        }, {
          encoder: HTTPUtil.Encoders.QUERY,
        }).then((models) => {
            const m = models[0];
            if (!m) return;

            const type = m.model.split('.')[1];
            dispatch(onModelCollectionAdd(type,
                models.reduce((acc, v) => {
                    if (v.model.toLowerCase() === `tracker.${type}`.toLowerCase()) {
                        v.fields.pk = v.pk;
                        acc.push(v.fields);
                    } else {
                        console.warn('unexpected model', v);
                    }
                    return acc;
                }, [])
            ));
            if (typeof command.done === 'function') {
                command.done();
            }
        }).catch(() => {
            if (typeof command.fail === 'function') {
                command.fail();
            }
        }).finally(() => {
            if (typeof command.always === 'function') {
                command.always();
            }
        });
    }
}

export default {
    loadModels,
    newDraftModel,
    deleteDraftModel,
    updateDraftModelField,
    setInternalModelField,
    saveDraftModels,
    saveField,
    command,
};
