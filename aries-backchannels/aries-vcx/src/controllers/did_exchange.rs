use std::sync::RwLock;

use actix_web::{get, post, web, Responder};
use aries_vcx_agent::aries_vcx::messages::msg_fields::protocols::did_exchange::request::Request as OobRequest;
use aries_vcx_agent::aries_vcx::messages::msg_fields::protocols::did_exchange::DidExchange;
use aries_vcx_agent::aries_vcx::messages::AriesMessage;

use crate::controllers::Request;
use crate::error::{HarnessError, HarnessErrorType, HarnessResult};
use crate::{soft_assert_eq, HarnessAgent};

#[derive(Deserialize)]
#[allow(dead_code)]
pub struct CreateResolvableDidRequest {
    their_public_did: String,
    their_did: String,
}

// This is so convoluted because of inaccurate data model
fn pthid_from_request(request: &OobRequest) -> HarnessResult<String> {
    request
        .decorators
        .thread
        .clone()
        .ok_or_else(|| {
            HarnessError::from_msg(
                HarnessErrorType::InvalidState,
                "Request does not contain a thread decorator",
            )
        })?
        .pthid
        .ok_or_else(|| {
            HarnessError::from_msg(
                HarnessErrorType::InvalidState,
                "Request does not contain a pthid",
            )
        })
}

impl HarnessAgent {
    pub async fn send_did_exchange_request(&self, invitation_id: &str) -> HarnessResult<String> {
        let invitation = self
            .aries_agent
            .out_of_band()
            .get_invitation(invitation_id)?;
        let id = self
            .aries_agent
            .did_exchange()
            .send_request_pairwise(invitation)
            .await?;
        Ok(json!({ "connection_id": id }).to_string())
    }

    pub async fn send_did_exchange_request_resolvable_did(
        &self,
        req: &CreateResolvableDidRequest,
    ) -> HarnessResult<String> {
        let id = self
            .aries_agent
            .did_exchange()
            .send_request_public(req.their_did.clone())
            .await?;
        Ok(json!({ "connection_id": id }).to_string())
    }

    pub async fn receive_did_exchange_request_resolvable_did(
        &self,
        msg_buffer: web::Data<RwLock<Vec<AriesMessage>>>,
    ) -> HarnessResult<String> {
        let request = {
            let mut request_guard = msg_buffer.write().or_else(|_| {
                Err(HarnessError::from_msg(
                    HarnessErrorType::InvalidState,
                    "Failed to lock message buffer",
                ))
            })?;
            request_guard.pop().ok_or_else(|| {
                HarnessError::from_msg(HarnessErrorType::InvalidState, "No message found")
            })?
        };
        if let AriesMessage::DidExchange(DidExchange::Request(request)) = request {
            let request_pthid = pthid_from_request(&request)?;
            Ok(json!({ "connection_id": request_pthid }).to_string())
        } else {
            Err(HarnessError::from_msg(
                HarnessErrorType::InvalidState,
                "Message is not a request",
            ))
        }
    }

    pub async fn send_did_exchange_response(
        &self,
        msg_buffer: web::Data<RwLock<Vec<AriesMessage>>>,
    ) -> HarnessResult<String> {
        let request = {
            let mut request_guard = msg_buffer.write().or_else(|_| {
                Err(HarnessError::from_msg(
                    HarnessErrorType::InvalidState,
                    "Failed to lock message buffer",
                ))
            })?;
            request_guard.pop().ok_or_else(|| {
                HarnessError::from_msg(HarnessErrorType::InvalidState, "No message found")
            })?
        };
        if let AriesMessage::DidExchange(DidExchange::Request(request)) = request {
            let request_pthid = pthid_from_request(&request)?;
            if !request_pthid.starts_with("did:sov:") // i.e. not implicit invitation
                && !self.aries_agent.out_of_band().exists_by_id(&request_pthid)
            {
                return Err(HarnessError::from_msg(
                    HarnessErrorType::ProtocolError,
                    &format!("No invitation found with id {request_pthid}"),
                ));
            }
            let invitation = self
                .aries_agent
                .out_of_band()
                .get_invitation(&request_pthid)?;
            let id = self
                .aries_agent
                .did_exchange()
                .send_response(request.clone().into(), invitation)
                .await?;
            Ok(json!({ "connection_id": id }).to_string())
        } else {
            Err(HarnessError::from_msg(
                HarnessErrorType::InvalidState,
                "Message is not a request",
            ))
        }
    }

    pub async fn get_did_exchange_state(&self, id: &str) -> HarnessResult<String> {
        let state = self.aries_agent.did_exchange().get_state(id)?;
        Ok(json!({ "state": state }).to_string())
    }

    pub async fn get_invitation_id(&self, id: &str) -> HarnessResult<String> {
        let invitation_id = self.aries_agent.did_exchange().invitation_id(id)?;
        Ok(json!({ "connection_id": invitation_id }).to_string())
    }
}

#[post("/send-request")]
async fn send_did_exchange_request(
    req: web::Json<Request<()>>,
    agent: web::Data<RwLock<HarnessAgent>>,
) -> impl Responder {
    agent
        .read()
        .unwrap()
        .send_did_exchange_request(&req.id)
        .await
}

#[post("/create-request-resolvable-did")]
async fn send_did_exchange_request_resolvable_did(
    req: web::Json<Request<Option<CreateResolvableDidRequest>>>,
    agent: web::Data<RwLock<HarnessAgent>>,
) -> impl Responder {
    agent
        .read()
        .unwrap()
        .send_did_exchange_request_resolvable_did(req.data.as_ref().ok_or(
            HarnessError::from_msg(
                HarnessErrorType::InvalidJson,
                "Failed to deserialize pairwise invitation",
            ),
        )?)
        .await
}

// TODO: Here we receive the outpout of create-request-resolvable-did
#[post("/receive-request-resolvable-did")]
async fn receive_did_exchange_request_resolvable_did(
    agent: web::Data<RwLock<HarnessAgent>>,
    msg_buffer: web::Data<RwLock<Vec<AriesMessage>>>,
) -> impl Responder {
    agent
        .read()
        .unwrap()
        .receive_did_exchange_request_resolvable_did(msg_buffer)
        .await
}

#[post("/send-response")]
async fn send_did_exchange_response(
    req: web::Json<Request<()>>,
    agent: web::Data<RwLock<HarnessAgent>>,
    msg_buffer: web::Data<RwLock<Vec<AriesMessage>>>,
) -> impl Responder {
    agent
        .read()
        .unwrap()
        .send_did_exchange_response(msg_buffer)
        .await
}

#[get("/{thread_id}")]
async fn get_invitation_id(
    agent: web::Data<RwLock<HarnessAgent>>,
    path: web::Path<String>,
) -> impl Responder {
    agent
        .read()
        .unwrap()
        .get_invitation_id(&path.into_inner())
        .await
}

#[get("/{thread_id}")]
pub async fn get_did_exchange_state(
    agent: web::Data<RwLock<HarnessAgent>>,
    path: web::Path<String>,
) -> impl Responder {
    agent
        .read()
        .unwrap()
        .get_did_exchange_state(&path.into_inner())
        .await
}

pub fn config(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/command/did-exchange")
            .service(send_did_exchange_request)
            .service(send_did_exchange_response)
            .service(receive_did_exchange_request_resolvable_did)
            .service(send_did_exchange_request_resolvable_did)
            .service(get_did_exchange_state),
    )
        .service(web::scope("/response/did-exchange").service(get_invitation_id));
}
